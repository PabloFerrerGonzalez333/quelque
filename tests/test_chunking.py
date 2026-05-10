from quelque.chunking import build_chunk_ranges


def test_build_chunk_ranges_with_overlap():
    ranges = build_chunk_ranges(
        duration_seconds=1000,
        chunk_duration_seconds=300,
        overlap_seconds=30,
    )
    assert ranges[0] == (0.0, 300.0)
    assert ranges[1] == (270.0, 570.0)
    assert ranges[-1][1] == 1000
