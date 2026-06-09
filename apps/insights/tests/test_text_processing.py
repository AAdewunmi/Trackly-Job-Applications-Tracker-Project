"""
Unit tests for NLTK-backed text preprocessing.
"""

import pytest

from apps.insights.nlp import preprocess_text as package_preprocess_text
from apps.insights.nlp.text_processing import (
    NLTKDataUnavailable,
    ensure_nltk_data_available,
    fallback_lemmatise,
    normalise_token,
    preprocess_text,
    preprocess_tokens,
)


def test_package_exports_preprocessing_helpers() -> None:
    """The NLP package should expose preprocessing helpers for services."""
    assert package_preprocess_text("Python developer") == preprocess_text(
        "Python developer"
    )


def test_normalise_token_lowercases_and_removes_noise() -> None:
    """Token normalisation should remove unsupported punctuation."""
    assert normalise_token("Django,") == "django"
    assert normalise_token("REST!") == "rest"


def test_preprocess_tokens_filters_stop_words() -> None:
    """Preprocessing should remove common low-value terms."""
    tokens = preprocess_tokens("We are hiring a Python developer for the team")

    assert "python" in tokens
    assert "developer" in tokens
    assert "we" not in tokens
    assert "team" not in tokens


def test_ensure_nltk_data_available_passes_when_runtime_data_exists(
    monkeypatch,
) -> None:
    """The runtime-data check should pass when every lookup path resolves."""
    monkeypatch.setattr(
        "apps.insights.nlp.text_processing._nltk_data_exists",
        lambda lookup_paths: True,
    )

    ensure_nltk_data_available()


def test_ensure_nltk_data_available_raises_actionable_error_when_data_missing(
    monkeypatch,
) -> None:
    """Missing runtime data should fail with a setup command."""
    monkeypatch.setattr(
        "apps.insights.nlp.text_processing._nltk_data_exists",
        lambda lookup_paths: "corpora/wordnet" not in lookup_paths,
    )

    with pytest.raises(NLTKDataUnavailable, match="make nltk-data"):
        ensure_nltk_data_available()


def test_preprocess_tokens_keeps_technical_terms() -> None:
    """Preprocessing should preserve useful technical terms."""
    tokens = preprocess_tokens("Python, Django, REST APIs, PostgreSQL, and CI/CD")

    assert "python" in tokens
    assert "django" in tokens
    assert "postgresql" in tokens


def test_fallback_lemmatise_reduces_common_inflections() -> None:
    """Fallback lemmatisation should handle common role-description forms."""
    assert fallback_lemmatise("testing") == "test"
    assert fallback_lemmatise("tested") == "test"
    assert fallback_lemmatise("applications") == "application"


def test_preprocess_text_returns_stable_string() -> None:
    """Preprocessed text should be safe to pass into TF-IDF vectorisation."""
    result = preprocess_text("Building tested Django services and APIs.")

    assert isinstance(result, str)
    assert "django" in result
    assert "service" in result or "services" in result


def test_preprocess_text_handles_empty_input() -> None:
    """Empty input should return an empty string."""
    assert preprocess_text("") == ""
