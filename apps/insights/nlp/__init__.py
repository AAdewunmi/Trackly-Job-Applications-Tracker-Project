"""
Retrieval-style NLP utilities for Trackly insights.

The package contains preprocessing, runtime-data, and similarity helpers for
the insight generation service.
"""

from apps.insights.nlp.similarity import (
    TextSimilarityResult,
    analyse_text_similarity,
    build_target_profile_text,
)
from apps.insights.nlp.text_processing import (
    NLTKDataUnavailable,
    ensure_nltk_data_available,
    preprocess_text,
    preprocess_tokens,
)

__all__ = [
    "NLTKDataUnavailable",
    "TextSimilarityResult",
    "analyse_text_similarity",
    "build_target_profile_text",
    "ensure_nltk_data_available",
    "preprocess_text",
    "preprocess_tokens",
]
