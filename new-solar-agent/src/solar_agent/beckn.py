"""
Pydantic models for the Beckn protocol, tailored for the Solar Agent's client role (BAP).
These models define the structure for creating a 'search' request.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BecknContext(BaseModel):
    """
    The context object for a Beckn request, originating from the BAP (Solar Agent).
    """
    domain: str = "dsep:energy"
    country: str = "IND"
    city: str = "std:080"
    action: str = "search"
    core_version: str = "1.0.0"
    bap_id: str
    bap_uri: str
    bpp_id: str
    bpp_uri: str
    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# --- Components for the 'search' Message ---

class BecknSearchItemDescriptor(BaseModel):
    name: str

class BecknSearchItem(BaseModel):
    descriptor: BecknSearchItemDescriptor

class BecknSearchCustomer(BaseModel):
    id: str

class BecknSearchFulfillment(BaseModel):
    customer: BecknSearchCustomer

class BecknSearchPayment(BaseModel):
    collection_amount: str = Field(..., alias="@ondc/org/collection_amount")


class BecknSearchIntent(BaseModel):
    item: BecknSearchItem
    fulfillment: BecknSearchFulfillment
    payment: BecknSearchPayment


class BecknSearchMessage(BaseModel):
    intent: BecknSearchIntent


class BecknSearchRequest(BaseModel):
    """The complete 'search' request payload sent by the Solar Agent."""
    context: BecknContext
    message: BecknSearchMessage

# --- Models for the 'on_search' callback (from Utility Agent) ---

class BecknOnSearchPayload(BaseModel):
    """
    This model is a placeholder for what the Solar Agent would expect
    to receive on its /beckn/on_search endpoint.
    It is NOT used for sending requests.
    """
    # This would be defined based on the BPP's response structure.
    # For now, we can just acknowledge receipt.
    provider: dict # Example field
    pass 