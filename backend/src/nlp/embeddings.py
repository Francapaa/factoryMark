"""Embeddings baseline con TF-IDF.

Wave 2: reemplazar por `sentence-transformers` multilingüe
(`paraphrase-multilingual-mpnet-base-v2`) manteniendo esta misma firma.
"""

from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    matrix = TfidfVectorizer(max_features=512).fit_transform(texts)
    return matrix.toarray().tolist()
