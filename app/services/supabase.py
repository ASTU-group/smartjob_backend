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


