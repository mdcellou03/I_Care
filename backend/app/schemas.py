"""Response models for the API. These define the JSON the frontend receives."""

from typing import Literal

from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    """Educational info for the predicted class (content comes from ml/recommendation.py)."""

    title: str
    description: str
    next_steps: list[str]
    urgency: str
    urgent_warning: str


class AnalyzeResponse(BaseModel):
    """Successful result of POST /api/v1/analyze."""

    status: Literal["success"] = "success"
    predicted_class: str
    confidence: float = Field(ge=0, le=1)
    # Probability for every class, so the UI can show how sure the model is
    # instead of only the top label.
    scores: dict[str, float]
    # True when the model isn't sure; the UI should suggest retaking the photo.
    low_confidence: bool
    recommendation: Recommendation
    disclaimer: str