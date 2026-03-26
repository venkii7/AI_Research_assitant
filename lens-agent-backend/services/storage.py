"""Cloudflare R2 file storage operations."""
import boto3
from botocore.config import Config
from core.config import get_settings
import uuid

settings = get_settings()

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
    aws_access_key_id=settings.r2_access_key_id,
    aws_secret_access_key=settings.r2_secret_access_key,
    config=Config(signature_version="s3v4"),
    region_name="auto",
)


async def upload_pdf(file_bytes: bytes, user_id: str) -> str:
    """Upload a PDF to R2 and return the storage key."""
    key = f"papers/{uuid.uuid4()}.pdf"
    s3.put_object(
        Bucket=settings.r2_bucket_name,
        Key=key,
        Body=file_bytes,
        ContentType="application/pdf",
        Metadata={"user_id": user_id},
    )
    return key


async def get_pdf_url(key: str) -> str:
    """Get a pre-signed URL for a PDF (valid 1 hour)."""
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.r2_bucket_name, "Key": key},
        ExpiresIn=3600,
    )


async def delete_pdf(key: str):
    """Delete a PDF from R2."""
    s3.delete_object(Bucket=settings.r2_bucket_name, Key=key)
