from fastapi import APIRouter, Depends, HTTPException, status
from app.services.supabase import supabase
from app.api.deps import get_current_user
from app.core.models import JobRead
import uuid

router = APIRouter(prefix="/saved-jobs", tags=["Saved Jobs"])