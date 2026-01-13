from fastapi import APIRouter
from app.api.v1 import auth, profile, jobs, applications, saved_jobs

router = APIRouter(prefix="/api/v1")


router.include_router(auth.router)
router.include_router(profile.router)
router.include_router(jobs.router)
router.include_router(applications.router)
router.include_router(saved_jobs.router)
