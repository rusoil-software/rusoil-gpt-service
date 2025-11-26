import pytest

from backend.app.embeddings import EmbeddingEngine, chunk_text


def test_encode_deterministic():
    e = EmbeddingEngine(dim=4)
    a = e.encode("hello world")
    b = e.encode("hello world")
    assert a == b
    assert len(a) == 4


def test_encode_type_error():
    e = EmbeddingEngine()
    with pytest.raises(TypeError):
        e.encode(123)


def test_encode_input_too_large():
    e = EmbeddingEngine(max_input_chars=10)
    with pytest.raises(ValueError):
        e.encode("a" * 11)


def test_encode_batch():
    e = EmbeddingEngine(dim=2)
    out = e.encode_batch(["a", "b"])
    assert isinstance(out, list)
    assert len(out) == 2
    assert len(out[0]) == 2


def test_chunk_text_basic():
    t = "abcdefghij"
    chunks = chunk_text(t, chunk_size=4, overlap=1)
    # expected: [abcd, d efg? let's just check concatenation equals original]
    recon = "".join(chunks)
    assert recon == t


def test_chunk_text_boundary():
    t = "a" * 10
    chunks = chunk_text(t, chunk_size=10, overlap=0)
    assert len(chunks) == 1
    assert chunks[0] == t


def test_chunk_overlap():
    t = "abcdefgh"
    chunks = chunk_text(t, chunk_size=4, overlap=2)
    # chunks: abcd, cd ef, efgh -> verify overlaps present
    assert chunks[0][-2:] == chunks[1][:2]


def test_chunk_invalid_args():
    with pytest.raises(ValueError):
        chunk_text("a", chunk_size=0)
    with pytest.raises(ValueError):
        chunk_text("a", chunk_size=4, overlap=5)
