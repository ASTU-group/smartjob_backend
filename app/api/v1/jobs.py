from fastapi import APIRouter, Depends, HTTPException, status
from app.services.supabase import supabase
from app.api.deps import get_current_user
from app.core.models import JobCreate, JobRead
from app.utils.notifications import trigger_job_screening
from fastapi import BackgroundTasks
import uuid

router = APIRouter(prefix="/jobs", tags=["Jobs"])