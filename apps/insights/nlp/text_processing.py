"""
Text preprocessing utilities for retrieval-style job description analysis.

The pipeline uses NLTK tokenisation and WordNet lemmatisation when local NLTK
corpora are available. A small deterministic fallback keeps tests and container
startup reliable when corpora have not been downloaded.
"""

import re

import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import TreebankWordTokenizer

REQUIRED_NLTK_DATA = {
    "tokenizers/punkt": "punkt",
    "corpora/wordnet": "wordnet",
    "corpora/omw-1.4": "omw-1.4",
    "corpora/stopwords": "stopwords",
}

STOP_WORDS = frozenset(
    {
        "a",
        "able",
        "about",
        "across",
        "after",
        "all",
        "also",
        "an",
        "and",
        "any",
        "are",
        "as",
        "at",
        "be",
        "because",
        "been",
        "being",
        "by",
        "can",
        "candidate",
        "company",
        "could",
        "day",
        "do",
        "each",
        "for",
        "from",
        "has",
        "have",
        "in",
        "into",
        "is",
        "it",
        "its",
        "job",
        "more",
        "must",
        "of",
        "on",
        "or",
        "our",
        "role",
        "should",
        "team",
        "that",
        "the",
        "their",
        "this",
        "to",
        "using",
        "we",
        "will",
        "with",
        "work",
        "you",
        "your",
    }
)

TOKENISER = TreebankWordTokenizer()
LEMMATISER = WordNetLemmatizer()


class NLTKDataUnavailable(RuntimeError):
    """Raised when required NLTK runtime data has not been provisioned."""


def ensure_nltk_data_available() -> None:
    """Raise an actionable error if required NLTK runtime data is missing."""
    missing_packages = [
        package_name
        for lookup_path, package_name in REQUIRED_NLTK_DATA.items()
        if not _nltk_data_exists(lookup_path)
    ]

    if missing_packages:
        packages = " ".join(missing_packages)
        raise NLTKDataUnavailable(
            "Missing required NLTK data. Run "
            f"`python -m nltk.downloader {packages}` or `make nltk-data`."
        )


def _nltk_data_exists(lookup_path: str) -> bool:
    """Return whether an NLTK data lookup path is available."""
    try:
        nltk.data.find(lookup_path)
    except LookupError:
        return False

    return True


def normalise_token(token: str) -> str:
    """Return a lower-case alphanumeric token suitable for vectorisation."""
    cleaned = re.sub(r"[^a-z0-9+#.-]", "", token.lower())
    cleaned = cleaned.strip(".-")
    return cleaned


def fallback_lemmatise(token: str) -> str:
    """Return a deterministic fallback lemma when NLTK corpora are unavailable."""
    if token.endswith("ies") and len(token) > 4:
        return f"{token[:-3]}y"

    if token.endswith("ing") and len(token) > 5:
        return token[:-3]

    if token.endswith("ed") and len(token) > 4:
        return token[:-2]

    if token.endswith("s") and len(token) > 3 and not token.endswith("ss"):
        return token[:-1]

    return token


def lemmatise_token(token: str) -> str:
    """Return the most compact WordNet lemma available for a token."""
    try:
        candidates = [
            LEMMATISER.lemmatize(token, pos="v"),
            LEMMATISER.lemmatize(token, pos="n"),
            LEMMATISER.lemmatize(token, pos="a"),
            LEMMATISER.lemmatize(token, pos="r"),
            token,
        ]
    except LookupError:
        return fallback_lemmatise(token)

    # Choosing the shortest candidate keeps forms like "testing" aligned with
    # "test" while preserving stable behaviour across repeated runs.
    return min(candidates, key=lambda value: (len(value), value))


def preprocess_tokens(text: str, min_length: int = 2) -> list[str]:
    """Return cleaned and lemmatised tokens for retrieval-style matching."""
    raw_tokens = TOKENISER.tokenize(text or "")
    processed_tokens: list[str] = []

    for raw_token in raw_tokens:
        token = normalise_token(raw_token)

        if not token:
            continue

        if len(token) < min_length:
            continue

        if token in STOP_WORDS:
            continue

        lemma = lemmatise_token(token)

        if lemma and lemma not in STOP_WORDS and len(lemma) >= min_length:
            processed_tokens.append(lemma)

    return processed_tokens


def preprocess_text(text: str) -> str:
    """Return whitespace-joined processed tokens for TF-IDF vectorisation."""
    return " ".join(preprocess_tokens(text))
