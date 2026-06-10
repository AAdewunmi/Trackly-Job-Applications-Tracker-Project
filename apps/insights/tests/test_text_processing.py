"""
Unit tests for NLTK-backed text preprocessing.
"""

import pytest

from apps.insights.nlp import preprocess_text as package_preprocess_text
from apps.insights.nlp.text_processing import (
    NLTKDataUnavailable,
    _nltk_data_exists,
    ensure_nltk_data_available,
    fallback_lemmatise,
    lemmatise_token,
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


def test_preprocess_tokens_filters_low_value_role_terms() -> None:
    """Preprocessing should remove low-value role description terms."""
    tokens = preprocess_tokens("Target role using Python and Django about APIs")

    assert "python" in tokens
    assert "django" in tokens
    assert "api" in tokens
    assert "apis" not in tokens
    assert "and" not in tokens
    assert "about" not in tokens
    assert "target" not in tokens
    assert "role" not in tokens
    assert "using" not in tokens


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


def test_nltk_data_exists_returns_true_when_any_lookup_path_resolves(
    monkeypatch,
) -> None:
    """The lookup helper should accept extracted or zipped NLTK resources."""

    def fake_find(lookup_path: str) -> str:
        if lookup_path == "corpora/wordnet.zip":
            return lookup_path

        raise LookupError

    monkeypatch.setattr("apps.insights.nlp.text_processing.nltk.data.find", fake_find)

    assert _nltk_data_exists(("corpora/wordnet", "corpora/wordnet.zip")) is True


def test_nltk_data_exists_returns_false_when_no_lookup_paths_resolve(
    monkeypatch,
) -> None:
    """The lookup helper should report missing data when all paths fail."""
    monkeypatch.setattr(
        "apps.insights.nlp.text_processing.nltk.data.find",
        lambda lookup_path: (_ for _ in ()).throw(LookupError),
    )

    assert _nltk_data_exists(("corpora/missing", "corpora/missing.zip")) is False


def test_preprocess_tokens_keeps_technical_terms() -> None:
    """Preprocessing should preserve useful technical terms."""
    tokens = preprocess_tokens("Python, Django, REST APIs, PostgreSQL, and CI/CD")

    assert "python" in tokens
    assert "django" in tokens
    assert "api" in tokens
    assert "apis" not in tokens
    assert "postgresql" in tokens


def test_preprocess_tokens_skips_terms_that_become_stop_words_after_lemmatisation(
    monkeypatch,
) -> None:
    """Lemmatised stop words should not be appended to processed tokens."""
    monkeypatch.setattr(
        "apps.insights.nlp.text_processing.lemmatise_token",
        lambda token: "and",
    )

    assert preprocess_tokens("developer") == []


@pytest.mark.parametrize("lemma", ["", "x"])
def test_preprocess_tokens_skips_empty_or_short_lemmas(
    monkeypatch,
    lemma: str,
) -> None:
    """Empty or too-short lemmas should not be appended to processed tokens."""
    monkeypatch.setattr(
        "apps.insights.nlp.text_processing.lemmatise_token",
        lambda token: lemma,
    )

    assert preprocess_tokens("developer") == []


def test_fallback_lemmatise_reduces_common_inflections() -> None:
    """Fallback lemmatisation should handle common role-description forms."""
    assert fallback_lemmatise("testing") == "test"
    assert fallback_lemmatise("tested") == "test"
    assert fallback_lemmatise("applications") == "application"
    assert fallback_lemmatise("policies") == "policy"
    assert fallback_lemmatise("api") == "api"


def test_lemmatise_token_uses_fallback_when_wordnet_data_is_missing(
    monkeypatch,
) -> None:
    """Missing WordNet data should fall back to deterministic lemmatisation."""

    def missing_wordnet(token: str, pos: str) -> str:
        raise LookupError

    monkeypatch.setattr(
        "apps.insights.nlp.text_processing.LEMMATISER.lemmatize",
        missing_wordnet,
    )

    assert lemmatise_token("testing") == "test"


def test_preprocess_text_returns_stable_string() -> None:
    """Preprocessed text should be safe to pass into TF-IDF vectorisation."""
    result = preprocess_text("Building tested Django services and APIs.")

    assert isinstance(result, str)
    assert "django" in result
    assert "service" in result
    assert "api" in result


def test_preprocess_text_handles_empty_input() -> None:
    """Empty input should return an empty string."""
    assert preprocess_text("") == ""
