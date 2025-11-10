from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.services.supabase import upload_file
from app.api.v1 import router


description = """
Smart Job API helps you find your dream job or the perfect candidate. 🚀

## Features
* **Auth**: Secure JWT-based authentication with Supabase.
* **Jobs**: Create, update, and find job listings.
* **Applications**: Apply for jobs and track your application status.
* **Profiles**: Manage your persona as a job seeker or recruiter.
"""

tags_metadata = [
    {
        "name": "Authentication",
        "description": "Operations with users. The login logic is here.",
    },
    {
        "name": "Jobs",
        "description": "Manage job postings. Recruiters can create/edit, Job Seekers can view.",
    },
    {
        "name": "Applications",
        "description": "Manage job applications. Track status and apply.",
    },
    {
        "name": "Profile",
        "description": "Manage user profile information and assets.",
    },
]

app = FastAPI(
    title="Smart Job",
    description=description,
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)

origins = [
    "http://localhost:3000",        # React standard
    "http://localhost:4000",        # CRA dev server
    "http://localhost:5173",        # Vite dev server
    "https://smartjob.webcode.codes" # Production React frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router.router)


@app.post("/")
def home():
    return {"msg": "healthy"}


@app.get("/verify-email")
def verify_email_page(type: str = None, access_token: str = None):  # type: ignore
    return {"message": "Email verification link clicked. You can now log in via API."}
