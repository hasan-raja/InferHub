from pathlib import Path


def test_phase_three_proto_defines_worker_services():
    proto = Path("proto/inferhub/v1/inference.proto").read_text()

    assert "service LLMWorker" in proto
    assert "rpc Chat" in proto
    assert "rpc StreamChat" in proto
    assert "service ASRWorker" in proto
    assert "rpc Transcribe" in proto
    assert "service TTSWorker" in proto
    assert "rpc Synthesize" in proto
    assert "service VisionWorker" in proto
    assert "rpc Analyze" in proto

