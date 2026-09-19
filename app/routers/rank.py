from fastapi import APIRouter, UploadFile, File
from app.services.ranking_service import RankingService
from app.schemas.paper import RankResponse

router = APIRouter(prefix="/rank", tags=["rank"])
ranking_service = RankingService()


@router.post("/", response_model=RankResponse)
async def rank_reviewers(file: UploadFile = File(...)):
    contents = await file.read()
    top_reviewers = ranking_service.rank(contents)
    return {"filename": file.filename, "top_reviewers": top_reviewers}