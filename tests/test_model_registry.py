from app.db.schema import MODEL_SEEDS


def test_phase_two_model_seeds_cover_modalities():
    modalities = {seed[1] for seed in MODEL_SEEDS}
    families = {seed[0] for seed in MODEL_SEEDS}

    assert {"llm", "asr", "tts", "vision"} <= modalities
    assert {"llama", "qwen", "whisper", "groq-tts", "vision"} <= families

