from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
import uuid


# --------------------------
# ENUM
# --------------------------
class RoleEnum(str, Enum):
    job_seeker = "job_seeker"
    recruiter = "recruiter"


# --------------------------
# AUTH SCHEMAS
# --------------------------
class LoginSchema(BaseModel):
    email: EmailStr = Field(..., description="User's email address", example="user@example.com")
    password: str = Field(..., description="User's password", example="securePassword123")


class SignupJobSeeker(BaseModel):
    email: EmailStr = Field(..., description="User's email address", example="seeker@example.com")
    password: str = Field(..., description="User's password", min_length=6, example="seekerPass123")
    full_name: str = Field(..., description="User's full name", example="John Doe")
    role: RoleEnum = Field(RoleEnum.job_seeker, description="User role (defaults to job_seeker)")


class SignupRecruiter(BaseModel):
    email: EmailStr = Field(..., description="User's email address", example="hr@company.com")
    password: str = Field(..., description="User's password", min_length=6, example="recruiterPass123")
    company_name: str = Field(..., description="Official company name", example="TechCorp Inc.")
    role: RoleEnum = Field(RoleEnum.recruiter, description="User role (defaults to recruiter)")


class ForgotPasswordSchema(BaseModel):
    email: EmailStr


class ResendEmailSchema(BaseModel):
    email: EmailStr


class OAuthCompleteProfile(BaseModel):
    role: RoleEnum = Field(..., description="User role (job_seeker or recruiter)")
    full_name: str | None = Field(None, description="Full name (required for job seekers)", example="John Doe")
    company_name: str | None = Field(None, description="Company name (required for recruiters)", example="TechCorp Inc.")



# --------------------------
# JOB SCHEMAS
# --------------------------
class JobBase(BaseModel):
    title: str = Field(..., description="Job title", example="Senior Python Developer")
    desc: str = Field(..., description="Detailed job description", example="We are looking for a senior developer...")
    deadline: str | None = Field(None, description="Application deadline (ISO 8601)", example="2025-12-31T23:59:59Z")
    location: str | None = Field(None, description="Job location", example="Remote / New York, NY")
    is_remote: bool = Field(False, description="Whether the job is remote")
    job_type: str | None = Field(None, description="Employment type", example="Full-time")
    salary_min: int | None = Field(None, description="Minimum salary range", example=80000)
    salary_max: int | None = Field(None, description="Maximum salary range", example=120000)
    currency: str = Field("USD", description="Currency for salary", example="USD")
    requirements: list[str] = Field([], description="List of required skills/qualifications", example=["Python", "FastAPI", "PostgreSQL"])
    status: str = Field("open", description="Job posting status", example="open")


class JobCreate(JobBase):
    pass


class JobRead(JobBase):
    id: uuid.UUID
    recruiter_id: uuid.UUID
    created_at: str | None = None
    n8n_execution_id: str | None = Field(None, description="The ID of the n8n execution handling this job's screening")
    screening_completed_at: str | None = Field(None, description="Timestamp when the automated screening was completed")


# --------------------------
# APPLICATION SCHEMAS
# --------------------------
class ApplicationBase(BaseModel):
    job_id: uuid.UUID = Field(..., description="ID of the job being applied for")
    cover_letter: str | None = Field(None, description="Optional cover letter for the application", example="I am very interested in this position because...")


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    status: str = Field(..., description="Updated status of the application", example="interviewing") # "pending", "interviewing", "rejected", "hired"
    ai_score: int | None = Field(None, description="AI-generated suitability score (0-100)", example=85)
    ai_reason: str | None = Field(None, description="AI justification for the score", example="Strong Python and FastAPI experience.")


class ApplicationRead(ApplicationBase):
    id: uuid.UUID
    job_seeker_id: uuid.UUID
    created_at: str | None = None
    status: str = "pending"
    resume_url: str | None = None
    email: str | None = Field(None, description="Email of the applicant")
    ai_score: int | None = Field(None, description="AI-generated suitability score (0-100)")
    ai_reason: str | None = Field(None, description="AI justification for the score")


class ApplicationReadWithJob(ApplicationRead):
    job: JobRead | None = Field(None, description="Details of the job this application is for")

