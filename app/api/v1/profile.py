from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Body
from app.services.supabase import supabase, delete_file
from app.api.deps import get_current_user
from app.core.models import (
    JobSeekerUpdate, 
    RecruiterUpdate, 
    PasswordUpdate,
    DeleteAccountSchema
)

router = APIRouter(prefix="/profile", tags=["Profile"])



@router.get("/me", summary="Get Own Profile", description="Retrieve the profile of the currently authenticated user, including role-specific details.")
def get_my_profile(current_user = Depends(get_current_user)):
    """
    Get current user profile (Job Seeker or Recruiter).
    """
    user_id = current_user.id
    
    # Try finding in Job Seeker table
    seeker = supabase.table("job_seeker").select("*").eq("id", user_id).execute()
    if seeker.data:
        return {"role": "job_seeker", "profile": seeker.data[0], "email": current_user.email}
    
    # Try finding in Recruiter table
    recruiter = supabase.table("recruiters").select("*").eq("id", user_id).execute()
    if recruiter.data:
        return {"role": "recruiter", "profile": recruiter.data[0], "email": current_user.email}
        
    raise HTTPException(status_code=404, detail="Profile not found")

@router.put("/me", summary="Update Profile Details", description="Update the currently authenticated user's profile information. Accepts fields based on user role.")
def update_profile(
    update_data: dict = Body(..., example={"full_name": "Jane Smith", "headline": "DevOps Engineer"}), 
    current_user = Depends(get_current_user)
):
    """
    Update profile details. 
    Uses Pydantic models to validate and filter allowed fields.
    """
    user_id = current_user.id
    
    # 1. Determine Role and Validate Data
    table = None
    
    seeker = supabase.table("job_seeker").select("id").eq("id", user_id).execute()
    if seeker.data:
        table = "job_seeker"
        try:
            # Validate and filter with Pydantic
            update_model = JobSeekerUpdate(**update_data)
            clean_data = update_model.model_dump(exclude_unset=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid update data for job seeker: {str(e)}")
    else:
        recruiter = supabase.table("recruiters").select("id").eq("id", user_id).execute()
        if recruiter.data:
            table = "recruiters"
            try:
                # Validate and filter with Pydantic
                update_model = RecruiterUpdate(**update_data)
                clean_data = update_model.model_dump(exclude_unset=True)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid update data for recruiter: {str(e)}")
        else:
            raise HTTPException(status_code=404, detail="Profile not found")

    # 2. Update
    if not clean_data:
         raise HTTPException(status_code=400, detail="No valid data provided to update")

    try:
        response = supabase.table(table).update(clean_data).eq("id", user_id).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.put("/me/password", summary="Change Password", description="Update the currently authenticated user's password. Requires validation of the old password.")
def update_password(data: PasswordUpdate, current_user = Depends(get_current_user)):
    """
    Update password.
    Verifies old_password first by attempting to sign in.
    """
    # 1. Verify Old Password & Get Session
    from supabase import create_client
    from app.core.config import settings
    
    # Use a fresh client to avoid global state issues and ensure clean auth
    auth_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    try:
        # Attempt to sign in with old credentials
        auth_response = auth_client.auth.sign_in_with_password({
            "email": current_user.email,
            "password": data.old_password
        })
        
        if not auth_response.session:
             raise ValueError("Login failed")
             
    except Exception:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Incorrect old password."
        )

    # 2. Update Password
    try:
        # Supabase allows updating the authenticated user's password
        # Now auth_client has the session from the sign_in above
        auth_client.auth.update_user({
            "password": data.new_password
        })
        return {"message": "Password updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/me/avatar", summary="Upload Profile Picture", description="Upload or update the currently authenticated user's profile picture. Supports image files.")
def update_avatar(file: UploadFile = File(...), current_user = Depends(get_current_user)):
    """
    Update profile picture.
    Removes old picture if strictly necessary, or just overwrites if using same name.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
        
    user_id = current_user.id
    
    # Determine table
    table = "job_seeker"
    current_data = supabase.table("job_seeker").select("profile_picture_url").eq("id", user_id).execute()
    if not current_data.data:
        table = "recruiters"
        current_data = supabase.table("recruiters").select("profile_picture_url").eq("id", user_id).execute()
        if not current_data.data:
             raise HTTPException(status_code=404, detail="Profile not found")
    
    # Upload
    try:
        file_content = file.file.read()
        file_ext = file.filename.split('.')[-1]
        file_path = f"{user_id}_avatar.{file_ext}"
        
        # Overwrite is default behavior for Supabase if configured, or we delete first
        # Ideally we might want to delete the *old* one if the extension changed
        # For simplicity, we just upload
        
        public_url = supabase.storage.from_("avatars").upload(
            file_path, 
            file_content, 
            file_options={"content-type": file.content_type, "upsert": "true"}
        )
        # Note: upload returns a specific response object, or we use our helper?
        # Let's use the object direct method or our helper in services.
        # But wait, our helper `upload_file` generates a UUID name.
        # Here we want a consistent name or to specifically update the DB.
        
        # Let's use the storage client directly to handle upsert properly or specific naming
        # actually, getting the public URL is separate.
        
        # Re-using the logic from auth:
        # We need the Public URL. 
        # If we use upsert, the path remains valid.
        
        # Let's implement manually to be safe on 'upsert'
        res = supabase.storage.from_("avatars").upload(
            file_path,
            file_content,
            file_options={"upsert": "true", "content-type": file.content_type}
        )
        
        # Get Signed URL (valid for 1 year to avoid immediate expiration)
        # Note: In a real production app, you'd generate this on the fly during GET /me
        # but for now, we'll store a long-lived one to fix your immediate access issue.
        signed_url_resp = supabase.storage.from_("avatars").create_signed_url(file_path, 31536000)
        final_url = signed_url_resp.get("signedURL") if isinstance(signed_url_resp, dict) else getattr(signed_url_resp, "signed_url", None)
        
        if not final_url:
            # Fallback to public if signed fails
            final_url = supabase.storage.from_("avatars").get_public_url(file_path)

        # Update DB
        supabase.table(table).update({"profile_picture_url": final_url}).eq("id", user_id).execute()
        
        return {"message": "Avatar updated", "url": final_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/me/resume", summary="Upload Resume", description="Upload or update the currently authenticated job seeker's resume. Only PDF files are accepted.")
def update_resume(file: UploadFile = File(...), current_user = Depends(get_current_user)):
    """
    Update resume (Job Seeker only).
    """
    if file.content_type != "application/pdf":
         raise HTTPException(status_code=400, detail="Resume must be a PDF")

    user_id = current_user.id
    
    # Verify Role
    seeker = supabase.table("job_seeker").select("id").eq("id", user_id).execute()
    if not seeker.data:
         raise HTTPException(status_code=403, detail="Only job seekers can have a resume")
         
    try:
        file_content = file.file.read()
        file_path = f"{user_id}_resume.pdf"
        
        # Upsert file
        supabase.storage.from_("resumes").upload(
            file_path,
            file_content,
            file_options={"upsert": "true", "content-type": "application/pdf"}
        )
        
        # Get Signed URL (valid for 1 year)
        signed_url_resp = supabase.storage.from_("resumes").create_signed_url(file_path, 31536000)
        final_url = signed_url_resp.get("signedURL") if isinstance(signed_url_resp, dict) else getattr(signed_url_resp, "signed_url", None)

        if not final_url:
            final_url = supabase.storage.from_("resumes").get_public_url(file_path)
        
        # Update DB
        supabase.table("job_seeker").update({"resume_url": final_url}).eq("id", user_id).execute()
        
        return {"message": "Resume updated", "url": final_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/me/legal-document", summary="Upload Legal Document", description="Upload or update legal document for recruiter verification. Only PDF files are accepted. Recruiters only.")
def update_legal_document(file: UploadFile = File(...), current_user = Depends(get_current_user)):
    """
    Update legal document (Recruiter only).
    Sets is_verified to FALSE on upload - admin must manually verify.
    """
    if file.content_type != "application/pdf":
         raise HTTPException(status_code=400, detail="Legal document must be a PDF")

    user_id = current_user.id
    
    # Verify Role - must be recruiter
    recruiter = supabase.table("recruiters").select("id, is_verified").eq("id", user_id).execute()
    if not recruiter.data:
         raise HTTPException(status_code=403, detail="Only recruiters can upload legal documents")
         
    try:
        file_content = file.file.read()
        file_path = f"{user_id}_legal_document.pdf"
        
        # Upsert file to document bucket
        supabase.storage.from_("documents").upload(
            file_path,
            file_content,
            file_options={"upsert": "true", "content-type": "application/pdf"}
        )
        
        # Get Signed URL (valid for 1 year)
        signed_url_resp = supabase.storage.from_("documents").create_signed_url(file_path, 31536000)
        final_url = signed_url_resp.get("signedURL") if isinstance(signed_url_resp, dict) else getattr(signed_url_resp, "signed_url", None)

        if not final_url:
            final_url = supabase.storage.from_("documents").get_public_url(file_path)
        
        # Update DB - set legal_document_url and is_verified to FALSE
        res = supabase.table("recruiters").update({
            "legal_document_url": final_url,
            "is_verified": False
        }).eq("id", user_id).execute()
        
        updated_recruiter = res.data[0]
        
        return {
            "message": "Legal document uploaded successfully. Your account will be reviewed by an admin.", 
            "url": final_url,
            "is_verified": updated_recruiter.get("is_verified", False)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
