import io
import numpy as np
from sentence_transformers import SentenceTransformer

from app.services.pdf_service import PDFService
from app.core.config import settings


class RankingService:
    def __init__(self):
        self.pdf_service = PDFService()
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self._reviewer_profiles = None  # built lazily, cached in memory

    def _build_reviewer_profiles(self):
        papers = self.pdf_service.get_all_papers(settings.dataset_path)

        reviewer_texts = {}

        for paper in papers:
            info = self.pdf_service.extract_paper_info(paper["filepath"])
            text = f"{info['title']} {info['abstract']}".strip()

            if not text:
                continue

            reviewer_texts.setdefault(paper["reviewer"], []).append(text)

        profiles = {}

        for reviewer, texts in reviewer_texts.items():
            embeddings = self.model.encode(texts)
            profiles[reviewer] = np.mean(embeddings, axis=0)

        return profiles

    def _get_reviewer_profiles(self):
        if self._reviewer_profiles is None:
            self._reviewer_profiles = self._build_reviewer_profiles()
        return self._reviewer_profiles

    def rank(self, pdf_bytes, top_n=5):
        profiles = self._get_reviewer_profiles()

        text = self.pdf_service.extract_text(io.BytesIO(pdf_bytes))
        query_embedding = self.model.encode([text])[0]

        scores = []

        for reviewer, profile_embedding in profiles.items():
            score = self._cosine_similarity(query_embedding, profile_embedding)
            scores.append({"reviewer": reviewer, "score": float(score)})

        scores.sort(key=lambda x: x["score"], reverse=True)

        return scores[:top_n]

    @staticmethod
    def _cosine_similarity(a, b):
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))