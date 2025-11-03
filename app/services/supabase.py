from supabase import create_client
from app.core.config import settings
from pydantic import EmailStr
from typing import Optional, Literal
from uuid import uuid4

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def upload_file(
    bucket: str,
    file_data: bytes,
    file_name: str,
    *,
    content_type: Optional[str] = None,
    path_prefix: str = "uploads",
) -> str:
    """Upload bytes to a Supabase storage bucket and return the public URL."""
    key = f"{path_prefix}/{uuid4()}-{file_name}"

    file_options = {"content-type": content_type} if content_type else None
    result = supabase.storage.from_(bucket).upload(
        path=key, file=file_data, file_options=file_options  # type: ignore
    )

    error = (
        result.get("error")
        if isinstance(result, dict)
        else getattr(result, "error", None)
    )
    if error:
        message = getattr(error, "message", None) or str(error)
        raise ValueError(f"Supabase upload failed: {message}")

    public_url = supabase.storage.from_(bucket).get_public_url(key)
    if not public_url:
        raise ValueError("Could not resolve public URL for uploaded file")

    return public_url



def login(email: EmailStr, password: str) -> Optional[str]:
    # Use a temporary client to avoid polluting the global client's session
    temp_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    response = temp_client.auth.sign_in_with_password(
        {"email": email, "password": password}
    )
    print(response)
    token = getattr(response.session, "access_token", None)
    return token

def signup(
    email: EmailStr,
    password: str,
    role: Literal["job_seeker", "employer"],
) -> str:
    # Use a temporary client
    temp_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    response = temp_client.auth.sign_up(
        {
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "role": role,
                }
            },
        }
    )

    if not response.user:
        raise ValueError("Signup failed")

    return response.user



def reset_password(email: EmailStr) -> bool:
    try:
        # Preferred API shape (newer clients)
        resp = supabase.auth.reset_password_for_email(email=email)
    except Exception:
        # Fallback to older/api namespace
        try:
            resp = supabase.auth.reset_password_for_email(email)
        except Exception:
            return False

    # resp may be dict-like or an object with attributes
    # Normalize to check for errors
    error = None
    try:
        if isinstance(resp, dict):
            # supabase-py sometimes returns {'data': None, 'error': None}
            error = resp.get("error")
        else:
            error = getattr(resp, "error", None)
    except Exception:
        error = None

    if error:
        return False

    return True


def resend_verification_email(email: EmailStr) -> bool:
    """
    Resends the verification email to the user.
    """
    try:
        resp = supabase.auth.resend({"type": "signup", "email": email})
    except Exception:
        return False

    error = None
    try:
        if isinstance(resp, dict):
            error = resp.get("error")
        else:
            error = getattr(resp, "error", None)
    except Exception:
        error = None

    if error:
        return False

    return True
