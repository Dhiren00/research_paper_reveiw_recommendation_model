from pydantic import BaseModel
from typing import List


class PaperInfo(BaseModel):
    reviewer: str
    filename: str


class PaperListResponse(BaseModel):
    total_papers: int
    papers: List[PaperInfo]


class PaperExtraction(BaseModel):
    reviewer: str
    filename: str
    title: str
    abstract: str
    keywords: List[str]


class ReviewerScore(BaseModel):
    reviewer: str
    score: float


class RankResponse(BaseModel):
    filename: str
    top_reviewers: List[ReviewerScore]