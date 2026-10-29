"""Offline TF-IDF and logistic-regression intent classifier."""

import json
import logging
import pickle
from pathlib import Path
from typing import Any

import joblib
from nltk.tokenize import RegexpTokenizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

logger = logging.getLogger(__name__)
_TOKENIZER = RegexpTokenizer(r"\w+")


def tokenize(text: str) -> list[str]:
    """Tokenize locally without downloading NLTK corpora."""
    return _TOKENIZER.tokenize(text.lower())


def read_examples(path: Path) -> tuple[list[str], list[str]]:
    with path.open(encoding="utf-8") as source:
        data = json.load(source)
    if not isinstance(data, list) or not data:
        raise ValueError("Intent data must be a non-empty list.")
    texts, labels = [], []
    for item in data:
        if not isinstance(item, dict) or not item.get("tag") or not item.get("patterns"):
            raise ValueError("Each intent requires a tag and at least one pattern.")
        if not isinstance(item["patterns"], list):
            raise ValueError(f"Patterns for {item['tag']} must be a list.")
        for pattern in item["patterns"]:
            if not isinstance(pattern, str) or not pattern.strip():
                raise ValueError(f"Intent {item['tag']} has an empty or invalid pattern.")
            texts.append(pattern.strip())
            labels.append(item["tag"])
    if len(set(labels)) < 2:
        raise ValueError("At least two intent labels are required.")
    return texts, labels


def build_classifier() -> Pipeline:
    return Pipeline([
        ("features", FeatureUnion([
            ("word", TfidfVectorizer(
                lowercase=True, strip_accents="unicode", ngram_range=(1, 2),
                sublinear_tf=True, tokenizer=tokenize, token_pattern=None,
            )),
            ("character", TfidfVectorizer(
                lowercase=True, strip_accents="unicode", analyzer="char_wb",
                ngram_range=(3, 5), sublinear_tf=True,
            )),
        ])),
        ("classifier", LogisticRegression(
            max_iter=1500, class_weight="balanced", random_state=42, C=10,
        )),
    ])


class IntentClassifier:
    def __init__(self, model_path: Path, data_path: Path):
        self.model_path = model_path
        self.data_path = data_path
        self.pipeline: Pipeline
        if model_path.is_file():
            try:
                self.pipeline = joblib.load(model_path)
                self.pipeline.predict(["startup check"])
                return
            except (OSError, ValueError, EOFError, AttributeError, KeyError, ImportError, TypeError, pickle.UnpicklingError) as exc:
                logger.warning("Could not load the saved intent model; using bundled data: %s", exc)
        texts, labels = read_examples(data_path)
        self.pipeline = build_classifier().fit(texts, labels)

    def predict(self, text: str) -> tuple[str, float]:
        probabilities = self.pipeline.predict_proba([text])[0]
        index = int(probabilities.argmax())
        return str(self.pipeline.classes_[index]), float(probabilities[index])

    def save(self, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, destination)

    @staticmethod
    def validate_data(path: Path) -> tuple[list[str], list[str]]:
        return read_examples(path)
