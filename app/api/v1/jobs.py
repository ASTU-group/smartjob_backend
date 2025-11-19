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



@router.get("/my-jobs", summary="List My Jobs", description="Retrieve all jobs created by the authenticated recruiter (draft, open, closed).")
def get_my_jobs(current_user = Depends(get_current_user)):
    """
    Get all jobs created by the current recruiter.
    Returns Open, Closed, and Draft jobs.
    """
    user_id = current_user.id
    
    # Verify Recruiter Role
    # (Optional: strictly check role or just rely on getting jobs for this ID)
    # Ideally should check if they are a recruiter first
    
    try:
        # Check if user is a recruiter (cleanup later to use a dependency for recruiter_only)
        # For now, just query jobs by recruiter_id
        response = supabase.table("job").select("*").eq("recruiter_id", user_id).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/", summary="List All Jobs", description="Retrieve a list of all available job postings with optional search and filter parameters.")
def get_jobs(
    q: str | None = None,
    location: str | None = None,
    job_type: str | None = None,
    is_remote: bool | None = None,
    salary_min: int | None = None,
    salary_max: int | None = None,
    requirements: str | None = None,
    status: str = "open"
):
    """
    Get all jobs with optional search and filter parameters.
    
    Parameters:
    - **q**: Search in job title and description (case-insensitive)
    - **location**: Filter by location (case-insensitive partial match)
    - **job_type**: Filter by exact job type (e.g., "Full-time", "Part-time")
    - **is_remote**: Filter for remote jobs only (true/false)
    - **salary_min**: Filter jobs with salary_max >= this value
    - **salary_max**: Filter jobs with salary_min <= this value
    - **requirements**: Comma-separated skills to search for (job must have at least one)
    - **status**: Filter by job status (default: "open")
    """
    try:
        # Start with base query
        query = supabase.table("job").select("*")
        
        # Apply status filter (always applied)
        query = query.eq("status", status)
        
        # Apply text search on title and description
        if q:
            # PostgreSQL ilike for case-insensitive search
            # We'll need to use or_ logic, so we do it with multiple queries and merge
            # Since Supabase Python client doesn't support complex OR directly in a clean way,
            # we'll use a workaround with multiple filters
            query = query.or_(f"title.ilike.%{q}%,desc.ilike.%{q}%")
        
        # Filter by location
        if location:
            query = query.ilike("location", f"%{location}%")
        
        # Filter by job type
        if job_type:
            query = query.eq("job_type", job_type)
        
        # Filter by remote status
        if is_remote is not None:
            query = query.eq("is_remote", is_remote)
        
        # Filter by salary range
        if salary_min is not None:
            query = query.gte("salary_max", salary_min)
        
        if salary_max is not None:
            query = query.lte("salary_min", salary_max)
        
        # Filter by requirements (array contains any of the provided skills)
        if requirements:
            # Split comma-separated requirements
            req_list = [req.strip() for req in requirements.split(",")]
            # Use cs (contains) operator for array overlap
            # Format: requirements@@{skill1,skill2}
            query = query.overlaps("requirements", req_list)
        
        response = query.execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
