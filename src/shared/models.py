# src/shared/models.py
from pydantic import BaseModel, Field, validator
from datetime import datetime, timezone, timedelta
from typing import Literal, List, Optional
import uuid

def now_utc():
    return datetime.now(timezone.utc)

class EnergyOffer(BaseModel):
    offer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: str
    quantity_kwh: float = Field(..., gt=0)
    price_per_kwh: float = Field(..., gt=0)
    timestamp: datetime = Field(default_factory=now_utc)
    valid_until: datetime

    @validator('valid_until', pre=True, always=True)
    def set_and_validate_valid_until(cls, v):
        if isinstance(v, str):
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            v = dt
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v <= now_utc():
            raise ValueError('valid_until must be a future datetime')
        return v

class EnergyRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    requester_id: str
    quantity_kwh: float = Field(..., gt=0)
    max_price_per_kwh: Optional[float] = Field(None, gt=0)
    required_by_timestamp: datetime

class EnergyContract(BaseModel):
    contract_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bap_agent_id: str
    bpp_agent_id: str
    original_offer: EnergyOffer
    agreed_quantity_kwh: float = Field(..., gt=0)
    agreed_price_per_kwh: float = Field(..., gt=0)
    contract_confirmation_time: datetime = Field(default_factory=now_utc)
    fulfillment_start_time: datetime
    fulfillment_status: Literal['pending', 'in_progress', 'completed', 'failed'] = 'pending'

class AgentProfile(BaseModel):
    agent_id: str
    agent_type: Literal['utility', 'solar']
    current_role: Literal['BAP', 'BPP', 'IDLE'] = 'IDLE'
    current_energy_storage_kwh: float = 0.0
    max_capacity_kwh: float
    generation_rate_kw: float = 0.0
    consumption_rate_kw: float = 0.0

# --- Beckn UEI Protocol Models ---

class BecknContext(BaseModel):
    domain: str = "ONIX:energy"
    action: str
    version: str = "1.0.0"
    bap_id: Optional[str] = None
    bap_uri: Optional[str] = None
    bpp_id: Optional[str] = None
    bpp_uri: Optional[str] = None
    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=now_utc)
    ttl: int = 60

# --- ADDED MISSING MODELS ---
class BecknItem(BaseModel):
    id: str
    quantity: dict = {"selected": {"count": 1}}

class BecknOrder(BaseModel):
    provider: dict
    items: List[BecknItem]
    billing: dict = {"name": "P2P Agent", "email": "contact@p2p.agent"}

class BecknSelectMessage(BaseModel):
    order: dict # Simplified: contains selected item IDs

class BecknConfirmMessage(BaseModel):
    order: BecknOrder
# --- END OF ADDED MODELS ---

class BecknAck(BaseModel):
    message: dict = {"ack": {"status": "ACK"}}