from backend.services.retrieval import chunk_by_char

def test_short_text_returns_single_chunk():
    assert chunk_by_char("abc",10, 2) == ["abc"]

def test_exact_multiple():
    assert chunk_by_char("abcdefghij", 5, 0) == ["abcde", "fghij"]

def test_consecutive_chunks_overlap():
    chunks = chunk_by_char("abcdefghij", 5, 2)
    assert chunks[0][-2:] == chunks[1][:2]