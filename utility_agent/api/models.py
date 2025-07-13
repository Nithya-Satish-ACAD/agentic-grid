from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import datetime

# DER Agent Models
class DERAgent(BaseModel):
    id: str = Field(..., description="Unique identifier for the DER agent")
    type: str = Field(..., description="Type of DER: solar, battery, load")
    ip_address: Optional[str] = None
    status: str = Field(default="offline", description="Current status: online/offline")
    last_heartbeat: Optional[datetime.datetime] = None

class DERStatus(BaseModel):
    agent_id: str
    power_output: float = Field(..., description="Current power output in kW")
    flexibility: float = Field(..., description="Available flexibility in kW")
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

# Flexibility and Commitment Models
class FlexibilityPlan(BaseModel):
    agent_id: str
    amount: float = Field(..., description="Flexibility amount in kW")
    duration: int = Field(..., description="Duration in minutes")
    start_time: datetime.datetime
    status: str = Field(default="pending", description="pending/confirmed/rejected")

class Commitment(BaseModel):
    plan_id: str
    agent_id: str
    committed_amount: float
    timestamp: datetime.datetime

# Conflict Models
class Conflict(BaseModel):
    type: str = Field(..., description="Type of conflict: data_mismatch, priority, etc.")
    agents_involved: List[str]
    details: Dict[str, Any]
    resolved: bool = False
    resolution: Optional[str] = None

# Utility Agent State
class UtilityState(BaseModel):
    mode: str = Field(default="normal", description="normal/blackout/emergency")
    registered_ders: List[DERAgent] = []
    flexibility_plans: List[FlexibilityPlan] = []
    conflicts: List[Conflict] = []
    alerts: List[str] = []

# Event Bus and API Payloads (Beckn-compatible stubs)
class BecknMessage(BaseModel):
    context: Dict[str, Any] = Field(..., description="Beckn context object")
    message: Dict[str, Any] = Field(..., description="Beckn message payload")

class CurtailmentRequest(BaseModel):
    agent_id: str
    amount: float
    duration: int

class RegisterDERRequest(BaseModel):
    id: str
    type: str
    ip_address: Optional[str]
