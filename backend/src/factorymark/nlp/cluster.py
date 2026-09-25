"""Clustering de reviews: TF-IDF + KMeans con k automático."""

from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from factorymark.nlp.sentiment import score_sentiment
from factorymark.state import ReviewCluster


def _top_terms(vectorizer: TfidfVectorizer, centroid: np.ndarray, n: int = 3) -> str:
    terms = np.array(vectorizer.get_feature_names_out())
    return ", ".join(terms[np.argsort(centroid)[::-1][:n]])


def cluster_reviews(texts: list[str]) -> list[ReviewCluster]:
    cleaned = [t.strip() for t in texts if t and t.strip()]
    if not cleaned:
        return []
    if len(cleaned) < 6:
        sentiments = [score_sentiment(t) for t in cleaned]
        return [
            ReviewCluster(
                topic="general",
                count=len(cleaned),
                avg_sentiment=sum(sentiments) / len(sentiments),
                example_texts=cleaned[:3],
            )
        ]
    k = min(5, max(2, len(cleaned) // 6))
    vectorizer = TfidfVectorizer(max_features=512)
    matrix = vectorizer.fit_transform(cleaned)
    labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(matrix)
    clusters: list[ReviewCluster] = []
    for i in range(k):
        members = [t for t, lab in zip(cleaned, labels) if lab == i]
        if not members:
            continue
        sentiments = [score_sentiment(t) for t in members]
        centroid = np.asarray(matrix[labels == i].mean(axis=0)).ravel()
        clusters.append(
            ReviewCluster(
                topic=_top_terms(vectorizer, centroid),
                count=len(members),
                avg_sentiment=sum(sentiments) / len(sentiments),
                example_texts=members[:3],
            )
        )
    return sorted(clusters, key=lambda c: c.count, reverse=True)
