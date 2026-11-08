"""Response models for the API. These define the JSON the frontend receives."""

from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeResponse(BaseModel):
    """Successful result of POST /api/v1/analyze."""

    status: Literal["success"] = "success"
    predicted_class: str
    confidence: float = Field(ge=0, le=1)
    # Probability for every class, so the UI can show how sure the model is
    # instead of only the top label.
    scores: dict[str, float]
    disclaimer: str