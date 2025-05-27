from models import CustomerInfo, SavingsEstimate, LeadQualification
from typing import Dict

# Constants for calculations
AVERAGE_SOLAR_PANEL_EFFICIENCY = 0.20  # 20% efficiency
AVERAGE_INSTALLATION_COST_PER_WATT = 2.5  # $2.50 per watt
AVERAGE_ELECTRICITY_RATE = 0.12  # $0.12 per kWh
CO2_REDUCTION_PER_KWH = 0.0004  # tons of CO2 per kWh

def calculate_savings(customer_info: CustomerInfo) -> SavingsEstimate:
    """Calculate potential savings and system specifications."""
    # Calculate recommended system size based on roof space and efficiency
    max_system_size = (customer_info.roof_size * AVERAGE_SOLAR_PANEL_EFFICIENCY) / 1000  # Convert to kW
    
    # Calculate annual energy production
    annual_production = (max_system_size * 1000 *  # Convert to watts
                        customer_info.average_daily_sunlight * 365 *  # Annual hours
                        AVERAGE_SOLAR_PANEL_EFFICIENCY)  # System efficiency
    
    # Calculate annual savings
    annual_savings = annual_production * AVERAGE_ELECTRICITY_RATE
    
    # Calculate installation cost
    installation_cost = max_system_size * 1000 * AVERAGE_INSTALLATION_COST_PER_WATT
    
    # Calculate payback period
    payback_period = installation_cost / annual_savings
    
    # Calculate environmental impact
    environmental_impact = annual_production * CO2_REDUCTION_PER_KWH
    
    return SavingsEstimate(
        annual_savings=round(annual_savings, 2),
        payback_period=round(payback_period, 1),
        recommended_system_size=round(max_system_size, 2),
        estimated_installation_cost=round(installation_cost, 2),
        environmental_impact=round(environmental_impact, 2)
    )

def qualify_lead(customer_info: CustomerInfo, savings_estimate: SavingsEstimate) -> LeadQualification:
    """Qualify the lead based on customer information and potential savings."""
    # Calculate qualification score (0-100)
    score = 0
    
    # Monthly electricity cost factor (0-30 points)
    if customer_info.monthly_electricity_cost > 200:
        score += 30
    elif customer_info.monthly_electricity_cost > 100:
        score += 20
    else:
        score += 10
    
    # Roof space factor (0-20 points)
    if customer_info.roof_size > 1000:
        score += 20
    elif customer_info.roof_size > 500:
        score += 15
    else:
        score += 10
    
    # Sunlight factor (0-20 points)
    if customer_info.average_daily_sunlight > 5:
        score += 20
    elif customer_info.average_daily_sunlight > 4:
        score += 15
    else:
        score += 10
    
    # Interest factor (0-30 points)
    if customer_info.interested_in_installation:
        score += 30
    
    # Determine priority level
    if score >= 80:
        priority = "High"
    elif score >= 60:
        priority = "Medium"
    else:
        priority = "Low"
    
    # Generate notes
    notes = []
    if customer_info.monthly_electricity_cost > 200:
        notes.append("High monthly electricity costs indicate strong potential for savings")
    if customer_info.roof_size > 1000:
        notes.append("Large roof space available for optimal system installation")
    if customer_info.average_daily_sunlight > 5:
        notes.append("Excellent sunlight conditions for solar generation")
    
    return LeadQualification(
        is_qualified=score >= 60,
        qualification_score=score,
        priority_level=priority,
        notes=notes
    ) 