import base64

import pytest
from pydantic import ValidationError

from app.inference.schemas import LLMChatRequest, VisionAnalyzeRequest


def test_llm_chat_request_requires_messages():
    with pytest.raises(ValidationError):
        LLMChatRequest(messages=[])


def test_vision_request_accepts_base64_image():
    encoded = base64.b64encode(b"fake-image").decode("ascii")

    payload = VisionAnalyzeRequest(
        prompt="describe this image",
        images=[{"mime_type": "image/png", "content_base64": encoded}],
    )

    assert payload.images[0].content_base64 == encoded


def test_vision_request_rejects_image_without_content_or_url():
    with pytest.raises(ValidationError):
        VisionAnalyzeRequest(prompt="describe", images=[{"mime_type": "image/png"}])

