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

