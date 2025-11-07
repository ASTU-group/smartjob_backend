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

