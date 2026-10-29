"""Loads configurable FAQ content and retrieves intent-matched answers."""

import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class KnowledgeBase:
    def __init__(self, path: Path):
        with path.open(encoding="utf-8") as source:
            self.entries = json.load(source)
        if not isinstance(self.entries, list):
            raise ValueError("FAQ data must be a list.")
        self._vectorizer = TfidfVectorizer(
            lowercase=True, strip_accents="unicode", ngram_range=(1, 2),
        )
        self._corpus = [
            f"{item['question']} {' '.join(item.get('keywords', []))}"
            for item in self.entries
        ]
        self._matrix = self._vectorizer.fit_transform(self._corpus) if self._corpus else None

    def answer(self, query: str, intent: str) -> dict | None:
        candidates = [
            index for index, entry in enumerate(self.entries)
            if entry.get("intent") == intent
        ]
        if not candidates or self._matrix is None:
            return None
        vector = self._vectorizer.transform([query])
        similarities = cosine_similarity(vector, self._matrix[candidates]).ravel()
        best_position = int(similarities.argmax())
        if float(similarities[best_position]) < 0.08:
            return None
        return self.entries[candidates[best_position]]
