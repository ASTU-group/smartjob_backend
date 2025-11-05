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

