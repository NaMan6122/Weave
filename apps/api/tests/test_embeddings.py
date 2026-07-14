import math

from app.services.embeddings import EmbeddingService, EMBEDDING_DIM


class TestEmbedText:
    def test_returns_correct_dimension(self):
        vec = EmbeddingService.embed_text_sync("hello world")
        assert len(vec) == EMBEDDING_DIM
        assert EMBEDDING_DIM == 384

    def test_is_normalized(self):
        vec = EmbeddingService.embed_text_sync("some sample text for testing")
        norm = math.sqrt(sum(v * v for v in vec))
        assert abs(norm - 1.0) < 1e-6

    def test_empty_text_returns_zero_vector(self):
        vec = EmbeddingService.embed_text_sync("")
        assert all(v == 0.0 for v in vec)

    def test_deterministic(self):
        a = EmbeddingService.embed_text_sync("reproducible")
        b = EmbeddingService.embed_text_sync("reproducible")
        assert a == b


class TestComputeSimilarity:
    def test_returns_between_zero_and_one_for_similar(self):
        a = EmbeddingService.embed_text_sync("seo link building")
        b = EmbeddingService.embed_text_sync("seo backlink strategy")
        sim = EmbeddingService.compute_similarity(a, b)
        assert 0.0 <= sim <= 1.0

    def test_same_text_gives_similarity_near_one(self):
        vec = EmbeddingService.embed_text_sync("identical text here")
        sim = EmbeddingService.compute_similarity(vec, vec)
        assert abs(sim - 1.0) < 1e-6

    def test_different_text_gives_lower_similarity(self):
        a = EmbeddingService.embed_text_sync("quantum physics research")
        b = EmbeddingService.embed_text_sync("chocolate cake recipe baking")
        sim = EmbeddingService.compute_similarity(a, b)
        assert sim < 0.9
