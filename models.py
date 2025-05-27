from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class RoofType(str, Enum):
    FLAT = "flat"
    PITCHED = "pitched"
    OTHER = "other"

class CustomerInfo(BaseModel):
    monthly_electricity_cost: float = Field(..., description="Monthly electricity bill in dollars")
    roof_type: RoofType = Field(..., description="Type of roof")
    roof_size: float = Field(..., description="Available roof space in square feet")
    location: str = Field(..., description="Customer's location/region")
    average_daily_sunlight: float = Field(..., description="Average daily sunlight hours")
    interested_in_installation: bool = Field(..., description="Customer's interest in installation")

class SavingsEstimate(BaseModel):
    annual_savings: float = Field(..., description="Estimated annual savings in dollars")
    payback_period: float = Field(..., description="Estimated payback period in years")
    recommended_system_size: float = Field(..., description="Recommended system size in kW")
    estimated_installation_cost: float = Field(..., description="Estimated installation cost in dollars")
    environmental_impact: float = Field(..., description="Estimated CO2 reduction in tons per year")

class LeadQualification(BaseModel):
    is_qualified: bool = Field(..., description="Whether the lead is qualified")
    qualification_score: float = Field(..., description="Lead qualification score (0-100)")
    priority_level: str = Field(..., description="Lead priority level (High/Medium/Low)")
    notes: List[str] = Field(default_factory=list, description="Additional notes about the lead")

class AgentState(BaseModel):
    customer_info: Optional[CustomerInfo] = None
    savings_estimate: Optional[SavingsEstimate] = None
    lead_qualification: Optional[LeadQualification] = None
    conversation_history: List[str] = Field(default_factory=list)
    current_step: str = Field(default="initial_greeting") 