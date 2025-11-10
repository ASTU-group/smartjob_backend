from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.services.supabase import upload_file
from app.api.v1 import router


app = FastAPI(
    title="Smart Job",
    description=description,
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)
app.include_router(router.router)


@app.post("/")
def home():
    return {"msg": "healthy"}


@app.get("/verify-email")
def verify_email_page(type: str = None, access_token: str = None):  # type: ignore
    return {"message": "Email verification link clicked. You can now log in via API."}
