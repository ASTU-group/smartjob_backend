from fastapi import APIRouter, Depends, HTTPException, status
from app.services.supabase import supabase
from app.api.deps import get_current_user
from app.core.models import JobCreate, JobRead
from app.utils.notifications import trigger_job_screening
from fastapi import BackgroundTasks
import uuid

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create Job Posting", description="Create a new job posting. This endpoint is restricted to recruiters.")
async def create_job(
    job: JobCreate, 
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Create a new job posting.
    Only recruiters can create jobs.
    """
    user_id = current_user.id
    
    # Verify role - assuming role is stored in user_metadata or we need to check profile
    # For now, let's check user_metadata which Supabase Auth often populates
    user_meta = current_user.user_metadata or {}
    role = user_meta.get("role")
    
    # Validating role from metadata might be insecure if client can set it, 
    # but with Supabase Auth schema in 'signup', it's server-set.
    # Alternatively, check 'recruiters' table for existence of this ID.
    
    # Better approach: Try to fetch from recruiters table.
    recruiter_check = supabase.table("recruiters").select("id, is_verified").eq("id", user_id).execute()
    if not recruiter_check.data:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can post jobs."
        )
    
    # Check if recruiter is verified
    recruiter = recruiter_check.data[0]
    if not recruiter.get("is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must upload legal documents and be verified before posting jobs. Please upload your documents via /api/v1/profile/me/legal-document"
        )

    # Insert Job
    try:
        response = supabase.table("job").insert({
            "recruiter_id": user_id,
            "title": job.title,
            "desc": job.desc,
            "deadline": job.deadline,
            "location": job.location,
            "is_remote": job.is_remote,
            "job_type": job.job_type,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "currency": job.currency,
            "requirements": job.requirements,
            "status": job.status
        }).execute()
        
        job_data = response.data[0]
        
        # Trigger n8n screening workflow in background
        background_tasks.add_task(
            trigger_job_screening,
            job_id=str(job_data.get("id")),
            title=job_data.get("title"),
            deadline=job_data.get("deadline")
        )

        return job_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
