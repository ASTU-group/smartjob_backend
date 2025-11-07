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
