from enum import StrEnum
from pydantic import Field, BaseModel

class Sentiment(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

class Intent(StrEnum):
    BILLING_INQUIRY = "billing_inquiry"
    TECHNICAL_ISSUE = "technical_issue"
    REFUND_REQUEST = "refund_request"
    GENERAL_QUESTION = "general_question"

class TriageSchema(BaseModel):
    intent: Intent = Field(
        ...,
        description="Categorize the user's request into one of these intents."
    )
    sentiment: Sentiment = Field(
        ...,
        description="Determine the emotional tone of the user's message."
    )
    pii_detected: bool = Field(
        ...,
        description="True if the message contains Person Identifiable Information (names, phones, etc)."
    )