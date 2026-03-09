from __future__ import annotations
from typing import Annotated, Any, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    patient_name: str
    date_of_birth: str
    reason_for_visit: str
    insurance_id: str
    insurance_verified: bool
    appointment_slot: str


# Typed key constants
PATIENT_NAME = "patient_name"
DATE_OF_BIRTH = "date_of_birth"
REASON_FOR_VISIT = "reason_for_visit"
INSURANCE_ID = "insurance_id"
INSURANCE_VERIFIED = "insurance_verified"
APPOINTMENT_SLOT = "appointment_slot"
MESSAGES = "messages"