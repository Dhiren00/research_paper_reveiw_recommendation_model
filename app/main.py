from fastapi import FastAPI, UploadFile, File
from app.services.pdf_service import PDFService
from app.services.ranking_service import RankingService
from app.core.config import settings

app = FastAPI(
    title="Reviewer Recommendation API"
)

pdf_service = PDFService()
ranking_service = RankingService()


@app.get("/")
def home():

    papers = pdf_service.get_all_papers(settings.dataset_path)

    if not papers:
        return {
            "message": "No papers found"
        }

    return {
        "total_papers": len(papers),
        "papers": papers[:10]
    }


@app.get("/test-extraction/{paper_number}")
def test_extraction(paper_number: int):

    papers = pdf_service.get_all_papers(settings.dataset_path)

    if not papers:
        return {
            "message": "No papers found"
        }

    if paper_number < 0 or paper_number >= len(papers):
        return {
            "error": "Invalid paper number",
            "total_papers": len(papers)
        }

    paper = papers[paper_number]

    info = pdf_service.extract_paper_info(
        paper["filepath"]
    )

    return {
        "paper_number": paper_number,
        "reviewer": paper["reviewer"],
        "filename": paper["filename"],
        "title": info["title"],
        "abstract": info["abstract"],
        "keywords": info["keywords"]
    }


@app.get("/debug-paper/{paper_number}")
def debug_paper(paper_number: int):

    papers = pdf_service.get_all_papers(settings.dataset_path)

    if paper_number < 0 or paper_number >= len(papers):
        return {
            "error": "Invalid paper number"
        }

    paper = papers[paper_number]

    text = pdf_service.extract_text(
        paper["filepath"]
    )

    return {
        "filename": paper["filename"],
        "first_2500_characters": text[:2500]
    }


@app.post("/rank")
async def rank_reviewers(file: UploadFile = File(...)):

    contents = await file.read()

    top_reviewers = ranking_service.rank(contents)

    return {
        "filename": file.filename,
        "top_reviewers": top_reviewers
    }