"""Unit tests for transcription chunking logic."""

from src.pipeline.s05_create_transcription_chunks import build_chunks_for_segments


class SimpleSeg:
    def __init__(self, id, start, end, text, idx):
        self.id = id
        self.start = start
        self.end = end
        self.text = text
        self.segment_index = idx


def test_build_chunks_basic():
    # Create 6 segments with varying durations to test chunking
    # segments: durations -> 5, 8, 9, 7, 6, 4 => cumulative
    segs = [
        SimpleSeg(1, 0.0, 5.0, "one", 0),
        SimpleSeg(2, 5.0, 13.0, "two", 1),
        SimpleSeg(3, 13.0, 22.0, "three", 2),
        SimpleSeg(4, 22.0, 29.0, "four", 3),
        SimpleSeg(5, 29.0, 35.0, "five", 4),
        SimpleSeg(6, 35.0, 39.0, "six", 5),
    ]

    chunks = build_chunks_for_segments(segs)

    # Expect chunks that try to be between 20-30 seconds
    # First chunk should include segments 1..3 (0.0..22.0)
    assert chunks[0]['first_segment_id'] == 1
    assert chunks[0]['last_segment_id'] == 3

    # Second chunk should start overlapping by 1 segment (segment 3)
    assert chunks[1]['first_segment_id'] == 3

    # Ensure aggregated text is not filled by builder (it's None at builder stage)
    assert chunks[0]['text'] is None


def test_text_aggregation_in_pipeline_style():
    # Ensure that combining texts yields properly ordered concatenation
    segs = [
        SimpleSeg(10, 0.0, 4.0, "אחד", 0),
        SimpleSeg(11, 4.0, 12.0, "שתיים", 1),
        SimpleSeg(12, 12.0, 24.0, "שלוש", 2),
    ]

    # Use the builder to get ranges
    chunks = build_chunks_for_segments(segs)
    # Simulate the pipeline's aggregation for the first chunk: find indices and join texts
    first_seg_id = chunks[0]['first_segment_id']
    last_seg_id = chunks[0]['last_segment_id']
    first_idx = next(i for i, s in enumerate(segs) if s.id == first_seg_id)
    last_idx = next(i for i, s in enumerate(segs) if s.id == last_seg_id)
    texts = [s.text for s in segs[first_idx:last_idx + 1]]
    joined = ' '.join(t.strip() for t in texts if t is not None)

    assert joined == "אחד שתיים שלוש"
