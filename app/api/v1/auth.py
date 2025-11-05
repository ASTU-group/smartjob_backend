from typing import Literal, cast
from fastapi import APIRouter, HTTPException, status, Depends, Form, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from ...services import supabase
from ...core.models import (
    RoleEnum,
    LoginSchema,
    SignupJobSeeker,
    SignupRecruiter,
    ForgotPasswordSchema,
    ResendEmailSchema,
    OAuthCompleteProfile,
)
from ...api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


# --------------------------
# Login Route
# --------------------------
@router.post("/login", summary="User Login", description="Authenticate a user with email and password to receive a JWT access token.")
async def login_route(data: LoginSchema):
    try:
        token = supabase.login(data.email, data.password)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )



# --------------------------
# Swagger / OAuth2 Token Route
# --------------------------
@router.post("/token", summary="OAuth2 Token Login", description="OAuth2 compatible token login, used by Swagger UI. Accepts form data.")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, used by Swagger UI.
    """
    try:
        # form_data.username should be the email
        token = supabase.login(form_data.username, form_data.password)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )



# --------------------------
# Job Seeker Signup
# --------------------------
@router.post("/signup/job_seeker", status_code=status.HTTP_201_CREATED, summary="Job Seeker Signup", description="Register a new job seeker. Requires a resume upload (PDF) and optional profile picture.")
def signup_job_seeker(
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    resume: UploadFile = File(...),
    profile_picture: UploadFile = File(None),
    # Extended Fields
    headline: str = Form(None),
    bio: str = Form(None),
    skills: str = Form(None), # Comma-separated string, we'll convert to list
    years_experience: int = Form(None),
    phone_number: str = Form(None),
    linked_in_url: str = Form(None),
    portfolio_url: str = Form(None)
):
    """
    Sign up a job seeker with Resume and optional Profile Picture:
    1. Create user in Supabase Auth.
    2. Upload resume to 'resumes'.
    3. Upload profile picture (optional) to 'avatars'.
    4. Insert profile into 'job_seeker' table.
    """
    # Validate PDF
    if resume.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed for resumes."
        )
    
    # Validate Image (if provided)
    if profile_picture and not profile_picture.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed for profile picture."
        )

    # 1. Sign up in Supabase Auth
    user = supabase.signup(
        email,
        password,
        "job_seeker",
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Signup failed"
        )
    
    user_id = user.id
    resume_path = None
    pic_path = None

    try:
        # 2. Upload Resume
        file_content = resume.file.read()
        resume_path = f"{user_id}_resume.pdf"
        # We still use upload_file, but it returns a public URL we might ignore or we can bypass it
        supabase.supabase.storage.from_("resumes").upload(
            path=resume_path,
            file=file_content,
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )
        # Get Signed URL (1 year)
        resume_signed = supabase.supabase.storage.from_("resumes").create_signed_url(resume_path, 31536000)
        resume_url = resume_signed.get("signedURL") or resume_signed.get("signed_url")

        # 3. Upload Profile Picture (if provided)
        profile_pic_url = None
        if profile_picture:
            pic_content = profile_picture.file.read()
            pic_path = f"{user_id}_avatar.{profile_picture.filename.split('.')[-1]}"
            supabase.supabase.storage.from_("avatars").upload(
                path=pic_path,
                file=pic_content,
                file_options={"content-type": profile_picture.content_type, "upsert": "true"}
            )
            pic_signed = supabase.supabase.storage.from_("avatars").create_signed_url(pic_path, 31536000)
            profile_pic_url = pic_signed.get("signedURL") or pic_signed.get("signed_url")

        # Parse skills if provided
        skill_list = [s.strip() for s in skills.split(',')] if skills else []

        # 4. Insert into 'job_seeker' table
        supabase.supabase.table("job_seeker").insert({
            "id": user_id,
            "full_name": full_name,
            "resume_url": resume_url,
            "profile_picture_url": profile_pic_url,
            # Extended fields
            "headline": headline,
            "bio": bio,
            "skills": skill_list,
            "years_experience": years_experience,
            "phone_number": phone_number,
            "linked_in_url": linked_in_url,
            "portfolio_url": portfolio_url
        }).execute()
        
    except Exception as e:
        # Rollback: Delete files and user
        if resume_path:
            supabase.delete_file("resumes", resume_path)
        if pic_path:
            supabase.delete_file("avatars", pic_path)
        supabase.delete_user(user_id)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed and rolled back: {str(e)}"
        )

    return {
        "message": "Job seeker registered successfully. Resume uploaded.",
        "user_id": user_id
    }

# --------------------------
# Recruiter Signup
# --------------------------
@router.post("/signup/recruiter", status_code=status.HTTP_201_CREATED, summary="Recruiter Signup", description="Register a new recruiter/employer with company details and optional profile picture.")
def signup_recruiter(
    email: str = Form(...),
    password: str = Form(...),
    company_name: str = Form(...),
    profile_picture: UploadFile = File(None),
    # Extended fields
    about_company: str = Form(None),
    website_url: str = Form(None),
    industry: str = Form(None),
    company_size: str = Form(None),
    location: str = Form(None)
):
    """
    Sign up a recruiter/employer with Profile Picture:
    1. Create user in Supabase Auth.
    2. Upload profile picture (optional) to 'avatars'.
    3. Insert profile into 'recruiters' table in Supabase.
    """
    # Validate Image (if provided)
    if profile_picture and not profile_picture.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed for profile picture."
        )

    # 1. Sign up in Supabase Auth
    user = supabase.signup(
        email,
        password,
        "employer", 
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Signup failed"
        )
    
    user_id = user.id
    profile_pic_url = None
    pic_path = None

    try:
        # 2. Upload Profile Picture (if provided)
        if profile_picture:
            file_content = profile_picture.file.read()
            pic_path = f"{user_id}_avatar.{profile_picture.filename.split('.')[-1]}"
            profile_pic_url = supabase.upload_file(
                bucket="avatars",
                file_data=file_content,
                file_name=pic_path,
                content_type=profile_picture.content_type,
                path_prefix="" # Root of bucket
            )

        # 3. Insert into 'recruiters' table
        supabase.supabase.table("recruiters").insert({
            "id": user_id,
            "company": company_name,
            "profile_picture_url": profile_pic_url,
            # Extended fields
            "about_company": about_company,
            "website_url": website_url,
            "industry": industry,
            "company_size": company_size,
            "location": location,
            "email": email,
        }).execute()
    except Exception as e:
        # Rollback
        if pic_path:
             supabase.delete_file("avatars", pic_path)
        supabase.delete_user(user_id)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed and rolled back: {str(e)}"
        )

    return {
        "message": "Recruiter registered successfully. Please check your email to verify your account.",
        "user_id": user_id
    }


# --------------------------
# Forgot Password
# --------------------------
@router.post("/forgot-password", status_code=status.HTTP_200_OK, summary="Forgot Password", description="Sends a password reset email to the specified user email address.")
async def forgot_password_route(data: ForgotPasswordSchema):
    """
    Sends a password reset email to the user.
    """
    try:
        sent = supabase.reset_password(data.email)
        if not sent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to send reset email to {data.email}",
            )
        return {
            "message": "If an account with this email exists, a password reset link has been sent."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# --------------------------
# Resend Verification Email
# --------------------------
@router.post("/resend-verification", status_code=status.HTTP_200_OK, summary="Resend Verification Email", description="Resends a verification email to the user if they haven't verified their account yet.")
async def resend_verification_route(data: ResendEmailSchema):
    """
    Resends the verification email to the user.
    """
    try:
        sent = supabase.resend_verification_email(data.email)
        if not sent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to resend verification email to {data.email}. The user might already be verified or an error occurred.",
            )
        return {
            "message": f"Verification email has been resent to {data.email} if the account is unverified."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

