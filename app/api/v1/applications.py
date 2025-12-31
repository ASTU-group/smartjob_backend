from fastapi import APIRouter, Depends, HTTPException, status
from app.services.supabase import supabase
from app.api.deps import get_current_user
from app.core.models import ApplicationCreate, ApplicationUpdate, ApplicationReadWithJob
from app.utils.notifications import send_application_confirmation
from fastapi import BackgroundTasks

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.get("/me", summary="Get My Applications", description="Retrieve all applications submitted by the authenticated job seeker, including full job details with optional search and filters.")
def get_my_applications(
    current_user = Depends(get_current_user),
    q: str | None = None,
    status_filter: str | None = None,
    min_score: int | None = None,
    max_score: int | None = None
):
    """
    Get all applications for the current job seeker.
    Returns applications with full job details.
    Only job seekers can access this endpoint.
    
    Parameters:
    - **q**: Search by job title (case-insensitive)
    - **status_filter**: Filter by application status (e.g., "pending", "interviewing", "hired", "rejected")
    - **min_score**: Filter applications with ai_score >= this value
    - **max_score**: Filter applications with ai_score <= this value
    """
    user_id = current_user.id
    
    # 1. Verify user is a job seeker
    seeker_check = supabase.table("job_seeker").select("id").eq("id", user_id).execute()
    if not seeker_check.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only job seekers can view applications. Recruiters should use /applications/job/{job_id} to view applications for their jobs."
        )
    
    # 2. Fetch all applications for this job seeker with job details
    try:
        # Join with job table to get job details for each application
        query = supabase.table("application").select("*, job(*)").eq("job_seeker_id", user_id)
        
        # Apply status filter
        if status_filter:
            query = query.eq("status", status_filter)
        
        # Apply AI score filters
        if min_score is not None:
            query = query.gte("ai_score", min_score)
        
        if max_score is not None:
            query = query.lte("ai_score", max_score)
        
        # Order by newest first
        query = query.order("created_at", desc=True)
        
        response = query.execute()
        
        # If searching by job title, filter in Python (since we can't filter on joined table)
        if q and response.data:
            filtered_data = [
                app for app in response.data
                if app.get("job") and q.lower() in app["job"].get("title", "").lower()
            ]
            return filtered_data
        
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

