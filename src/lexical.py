"""Corpus-fitted TF-IDF cosine baseline; lexical, NOT semantic embeddings."""
import math
import re
import unicodedata
from collections import Counter


def tokens(text):
    return re.findall(r"\w+", unicodedata.normalize("NFC", text).lower())


class TfidfEmbedder:
    _backend_name = "lexical TF-IDF (not semantic)"

    @staticmethod
    def features(text):
        words = tokens(text)
        return words + [a + " " + b for a, b in zip(words, words[1:])]

    def __init__(self, documents):
        documents = list(documents)
        frequencies = Counter()
        for content in documents:
            frequencies.update(set(self.features(content)))
        self.vocabulary = sorted(frequencies)
        self.idf = [math.log((1 + len(documents)) / (1 + frequencies[w])) + 1 for w in self.vocabulary]

    def __call__(self, text):
        counts = Counter(self.features(text))
        vector = [(1 + math.log(counts[w])) * weight if counts[w] else 0.0
                  for w, weight in zip(self.vocabulary, self.idf)]
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]
