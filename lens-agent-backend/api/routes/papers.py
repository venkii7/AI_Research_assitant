"""Paper CRUD and submission endpoints."""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from api.dependencies import require_user_record, check_paper_limit
from services import supabase_client, storage, job_queue
from models.requests import ProcessPaperRequest
from models.responses import JobResponse, PaperResponse
from core.config import get_settings
import re

router = APIRouter(prefix="/api/papers", tags=["papers"])
settings = get_settings()


@router.post("/process", response_model=JobResponse, status_code=202)
async def process_paper(
    request: ProcessPaperRequest,
    user: dict = Depends(check_paper_limit),
):
    """
    Submit a paper for Smart Brief generation.
    Accepts an ArXiv ID, URL, or 'upload' (pair with multipart endpoint).
    Returns a job_id immediately. Poll /stream/{job_id} for progress.
    """
    paper_data = {"arxiv_id": None, "pdf_path": None}

    # Detect source type and extract ArXiv ID if applicable
    source = request.source.strip()
    if re.match(r"^\d{4}\.\d{4,5}", source):
        paper_data["arxiv_id"] = source
    elif "arxiv.org" in source:
        match = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", source)
        if match:
            paper_data["arxiv_id"] = match.group(1)

    # Create paper record
    paper = await supabase_client.create_paper(user["id"], paper_data)

    # Enqueue the agent job
    job_id = await job_queue.enqueue_paper_job(
        paper_id=paper["id"],
        user_id=user["id"],
        preferences=request.user_preferences,
    )

    return JobResponse(
        job_id=job_id,
        paper_id=paper["id"],
        status="queued",
        stream_url=f"/api/stream/{job_id}",
    )


@router.post("/upload", response_model=JobResponse, status_code=202)
async def upload_and_process(
    file: UploadFile = File(...),
    user: dict = Depends(check_paper_limit),
):
    """
    Upload a PDF file directly and submit for processing.
    Max file size: 50MB.
    """
    # Validate file type
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(
            status_code=415,
            detail={
                "error": "Only PDF files are supported",
                "code": "unsupported_format",
            },
        )

    # Validate file size
    contents = await file.read()
    max_bytes = settings.max_pdf_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail={
                "error": f"File exceeds {settings.max_pdf_size_mb}MB limit",
                "code": "file_too_large",
                "details": {
                    "size_mb": round(len(contents) / 1024 / 1024, 2),
                    "limit_mb": settings.max_pdf_size_mb,
                },
            },
        )

    # Upload to R2
    pdf_key = await storage.upload_pdf(contents, user["id"])

    # Create paper record
    paper = await supabase_client.create_paper(
        user["id"],
        {
            "pdf_path": pdf_key,
            "title": (
                file.filename.replace(".pdf", "")
                if file.filename
                else "Uploaded paper"
            ),
        },
    )

    # Enqueue
    job_id = await job_queue.enqueue_paper_job(paper["id"], user["id"], {})

    return JobResponse(
        job_id=job_id,
        paper_id=paper["id"],
        status="queued",
        stream_url=f"/api/stream/{job_id}",
    )


@router.get("", response_model=list[PaperResponse])
async def list_papers(
    status: str | None = Query(
        None, pattern="^(queued|processing|done|failed)$"
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: dict = Depends(require_user_record),
):
    """Return the authenticated user's papers, newest first."""
    papers = await supabase_client.list_papers(user["id"], status, limit, offset)
    return papers


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(paper_id: str, user: dict = Depends(require_user_record)):
    """Return a single paper with its full Smart Brief."""
    paper = await supabase_client.get_paper(paper_id, user["id"])
    if not paper:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Paper not found",
                "code": "not_found",
            },
        )
    return paper


@router.delete("/{paper_id}", status_code=204)
async def delete_paper(paper_id: str, user: dict = Depends(require_user_record)):
    """Soft-delete a paper and remove its PDF from R2."""
    paper = await supabase_client.get_paper(paper_id, user["id"])
    if not paper:
        raise HTTPException(
            status_code=404, detail={"error": "Not found", "code": "not_found"}
        )

    # Delete from R2 if exists
    if paper.get("pdf_path"):
        await storage.delete_pdf(paper["pdf_path"])

    await supabase_client.delete_paper(paper_id, user["id"])
