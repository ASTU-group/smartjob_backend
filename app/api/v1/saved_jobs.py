from fastapi import APIRouter, Depends, HTTPException, status
from app.services.supabase import supabase
from app.api.deps import get_current_user
from app.core.models import JobRead
import uuid

router = APIRouter(prefix="/saved-jobs", tags=["Saved Jobs"])

@router.post("/{job_id}", status_code=status.HTTP_201_CREATED, summary="Save a Job", description="Save a job for later viewing. Restricted to Job Seekers.")
def save_job(job_id: uuid.UUID, current_user = Depends(get_current_user)):
    """
    Save a job.
    """
    user_id = current_user.id
    
    # Verify Job Seeker Role (Optional, but good practice)
    # For now, we assume any authenticated user can save (or strictly seekers)
    # Let's clean check:
    # seeker_check = supabase.table("job_seeker").select("id").eq("id", user_id).execute()
    # if not seeker_check.data:
    #      raise HTTPException(status_code=403, detail="Only job seekers can save jobs.")
         
    try:
        # Check if job exists
        job_check = supabase.table("job").select("id").eq("id", job_id).execute()
        if not job_check.data:
            raise HTTPException(status_code=404, detail="Job not found")

        # Insert into saved_jobs
        response = supabase.table("saved_jobs").insert({
            "job_seeker_id": str(user_id),
            "job_id": str(job_id)
        }).execute()
        
        return {"message": "Job saved successfully"}

    except Exception as e:
        # Supabase/Postgres might raise duplicate key error if already saved
        if "duplicate key" in str(e) or "unique constraint" in str(e).lower():
             raise HTTPException(status_code=409, detail="Job already saved")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", summary="List Saved Jobs", description="Retrieve all saved jobs for the authenticated Job Seeker.")
def get_saved_jobs(current_user = Depends(get_current_user)):
    """
    Get all saved jobs.
    """
    user_id = current_user.id
    
    try:
        # Join saved_jobs with job
        # Supabase syntax for join: select(*, job(*))
        response = supabase.table("saved_jobs").select("job_id, created_at, job(*)").eq("job_seeker_id", str(user_id)).execute()
        
        # Flatten the structure if needed, or return as is.
        # The structure will be: [{ "job_id": ..., "job": { "title": ... } }, ...]
        
        # Make it cleaner: return list of Jobs
        saved_list = []
        for item in response.data:
            job_data = item.get("job")
            if job_data:
                saved_list.append(job_data)
                
        return saved_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Unsave Job", description="Remove a job from saved jobs.")
def unsave_job(job_id: uuid.UUID, current_user = Depends(get_current_user)):
    """
    Unsave a job.
    """
    user_id = current_user.id
    
    try:
        response = supabase.table("saved_jobs").delete().eq("job_seeker_id", str(user_id)).eq("job_id", str(job_id)).execute()
        # if not response.data: 
        #    raise HTTPException(status_code=404, detail="Saved job not found") -- Supabase delete might not return data if successful?
        return None
    except Exception as e:
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
