"""
Pydantic models for the Beckn/UEI protocol.

This module defines the data structures for requests and responses according
to the Beckn specification, tailored for the Unified Energy Interface (UEI) domain.
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
import uuid

# ==============================================================================
# Core Beckn Models
# ==============================================================================

class BecknContext(BaseModel):
    """
    The context object provides transaction-specific information that is used
    for tracking and routing messages.
    """
    domain: str = Field(..., example="dsep:energy")
    country: str = Field(..., example="IND")
    city: str = Field(..., example="std:080")
    action: str = Field(..., example="search")
    core_version: str = Field(..., example="1.0.0")
    bap_id: str = Field(..., example="solar-agent.example.com")
    bap_uri: str = Field(..., example="http://solar-agent.example.com/beckn/")
    bpp_id: str = Field(..., example="utility-agent.example.com")
    bpp_uri: str = Field(..., example="http://utility-agent.example.com/beckn/")
    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class BecknError(BaseModel):
    """Standard Beckn error structure."""
    type: str
    code: str
    path: Optional[str] = None
    message: str

class BecknResponse(BaseModel):
    """Represents a generic NACK (Negative Acknowledgement) response."""
    message: Dict[str, Dict[str, str]] = {"ack": {"status": "NACK"}}
    error: Optional[BecknError] = None

# ==============================================================================
# Search Message Models (search action)
# ==============================================================================

class SearchIntent(BaseModel):
    """Defines the user's intent in a search request."""
    item: Dict[str, Any] = Field(
        ...,
        description="Describes the item being searched for, e.g., electricity.",
        example={"descriptor": {"name": "r-APPC"}},
    )
    fulfillment: Dict[str, Any] = Field(
        ...,
        description="Describes when and where the fulfillment is required.",
        example={
            "type": "delivery",
            "start": {"time": {"timestamp": "2025-07-16T10:00:00Z"}},
            "end": {"time": {"timestamp": "2025-07-16T11:00:00Z"}},
        },
    )
    payment: Optional[Dict[str, Any]] = Field(
        None,
        description="Payment parameters.",
        example={"@ondc/org/buyer_app_finder_fee_amount": "0.0"},
    )

class SearchMessage(BaseModel):
    """The message payload for a 'search' action."""
    intent: SearchIntent

class SearchRequest(BaseModel):
    """The complete 'search' request payload."""
    context: BecknContext
    message: SearchMessage

# ==============================================================================
# On-Search Message Models (on_search action)
# ==============================================================================
# These are placeholders for now and will be expanded later.

class OnSearchMessage(BaseModel):
    """Message for an on_search action. Contains the catalog."""
    catalog: Dict[str, Any] = Field(..., description="The catalog of available energy items.")

class OnSearchRequest(BaseModel):
    """The complete 'on_search' response payload."""
    context: BecknContext
    message: OnSearchMessage
