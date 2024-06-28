from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from app.services.processors.pdf import muPDF, pdf_miner, pyPDF2, textract, tesseract
from app.services.processors.pdf.pdf_tasks import process_pdfs
from app.models.pdf_model import PDFTextResponse
from typing import List

router = APIRouter(
    prefix="/convert",
    tags=["convert"]
)

@router.post("/", response_model=List[PDFTextResponse])
async def convert_pdfs(files: List[UploadFile] = File(...)):
    try:
        responses = await process_pdfs(files)
        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
