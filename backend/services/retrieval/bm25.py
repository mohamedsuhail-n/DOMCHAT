import math
import re
from typing import List, Dict, Any

def tokenize(text: str) -> List[str]:
    # Lowercase and split on non-alphanumeric
    return [w for w in re.findall(r'\b[a-zA-Z0-9_]+\b', text.lower()) if len(w) > 1]

class BM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def score(self, query: str, documents: List[str]) -> List[float]:
        if not documents:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return [0.0] * len(documents)

        # Tokenize corpus
        doc_tokens = [tokenize(doc) for doc in documents]
        n_docs = len(documents)
        doc_lengths = [len(dt) for dt in doc_tokens]
        avg_doc_len = sum(doc_lengths) / max(1, n_docs)

        # Document frequencies for query terms
        df = {}
        for qt in query_tokens:
            df[qt] = sum(1 for dt in doc_tokens if qt in dt)

        # Calculate BM25 scores
        scores = []
        for i, dt in enumerate(doc_tokens):
            score = 0.0
            doc_len = doc_lengths[i]
            for qt in query_tokens:
                if qt not in dt:
                    continue
                # Term frequency in document
                tf = dt.count(qt)
                # IDF with smoothing
                n_qt = df.get(qt, 0)
                idf = math.log((n_docs - n_qt + 0.5) / (n_qt + 0.5) + 1.0)
                # Term weight
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / max(1, avg_doc_len)))
                score += idf * (numerator / max(0.001, denominator))
            scores.append(score)

        return scores
