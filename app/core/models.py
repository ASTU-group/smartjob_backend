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




# --------------------------
# PROFILE UPDATE SCHEMAS
# --------------------------
class JobSeekerUpdate(BaseModel):
    full_name: str | None = Field(None, description="Full name of the job seeker", example="Jane Doe")
    headline: str | None = Field(None, description="Professional headline", example="Passionate Full Stack Developer")
    bio: str | None = Field(None, description="Short biography", example="I have 5 years of experience in...")
    skills: list[str] | None = Field(None, description="List of skills", example=["React", "Node.js"])
    years_experience: int | None = Field(None, description="Years of professional experience", example=5)
    phone_number: str | None = Field(None, description="Contact phone number", example="+1234567890")
    linked_in_url: str | None = Field(None, description="LinkedIn profile URL", example="https://linkedin.com/in/janedoe")
    portfolio_url: str | None = Field(None, description="Portfolio or personal website URL", example="https://janedoe.dev")


class RecruiterUpdate(BaseModel):
    company: str | None = Field(None, description="Company name", example="Innovative Tech")
    about_company: str | None = Field(None, description="Description of the company", example="We build cutting edge solutions...")
    website_url: str | None = Field(None, description="Company website URL", example="https://innovative.tech")
    industry: str | None = Field(None, description="Industry sector", example="Technology")
    company_size: str | None = Field(None, description="Approximate number of employees", example="50-200")
    location: str | None = Field(None, description="Company headquarters location", example="San Francisco, CA")


class PasswordUpdate(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)


class DeleteAccountSchema(BaseModel):
    password: str = Field(..., description="User's current password to confirm deletion")
