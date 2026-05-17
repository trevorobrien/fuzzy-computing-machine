import pytest
from models import CustomerInfo
from utils import (
    calculate_savings,
    qualify_lead,
    AVERAGE_SOLAR_PANEL_EFFICIENCY,
    AVERAGE_INSTALLATION_COST_PER_WATT,
    AVERAGE_ELECTRICITY_RATE,
    CO2_REDUCTION_PER_KWH,
)


def make_customer(**overrides) -> CustomerInfo:
    defaults = dict(
        monthly_electricity_cost=150.0,
        roof_type="pitched",
        roof_size=1000.0,
        location="Austin",
        average_daily_sunlight=5.0,
        interested_in_installation=True,
    )
    defaults.update(overrides)
    return CustomerInfo(**defaults)


class TestCalculateSavings:
    def test_system_size_uses_efficiency_once(self):
        customer = make_customer(roof_size=1000.0, average_daily_sunlight=5.0)
        est = calculate_savings(customer)
        expected_kw = (1000.0 * AVERAGE_SOLAR_PANEL_EFFICIENCY) / 1000
        assert est.recommended_system_size == round(expected_kw, 2)

    def test_annual_production_no_double_efficiency(self):
        customer = make_customer(roof_size=1000.0, average_daily_sunlight=5.0)
        est = calculate_savings(customer)
        system_kw = (1000.0 * AVERAGE_SOLAR_PANEL_EFFICIENCY) / 1000
        expected_production = system_kw * 5.0 * 365
        expected_savings = round(expected_production * AVERAGE_ELECTRICITY_RATE, 2)
        assert est.annual_savings == expected_savings

    def test_payback_period_no_divide_by_zero(self):
        # With zero roof_size annual_savings will be 0; should not raise
        customer = make_customer(roof_size=0.0, average_daily_sunlight=0.0)
        est = calculate_savings(customer)
        assert est.payback_period == 0.0

    def test_installation_cost(self):
        customer = make_customer(roof_size=1000.0)
        est = calculate_savings(customer)
        system_kw = (1000.0 * AVERAGE_SOLAR_PANEL_EFFICIENCY) / 1000
        expected_cost = round(system_kw * 1000 * AVERAGE_INSTALLATION_COST_PER_WATT, 2)
        assert est.estimated_installation_cost == expected_cost

    def test_environmental_impact(self):
        customer = make_customer(roof_size=1000.0, average_daily_sunlight=5.0)
        est = calculate_savings(customer)
        system_kw = (1000.0 * AVERAGE_SOLAR_PANEL_EFFICIENCY) / 1000
        annual_production = system_kw * 5.0 * 365
        expected_impact = round(annual_production * CO2_REDUCTION_PER_KWH, 2)
        assert est.environmental_impact == expected_impact

    def test_payback_period_positive(self):
        customer = make_customer(roof_size=500.0, average_daily_sunlight=4.0)
        est = calculate_savings(customer)
        assert est.payback_period > 0

    def test_larger_roof_means_higher_savings(self):
        small = calculate_savings(make_customer(roof_size=500.0))
        large = calculate_savings(make_customer(roof_size=2000.0))
        assert large.annual_savings > small.annual_savings


class TestQualifyLead:
    def test_high_priority(self):
        customer = make_customer(
            monthly_electricity_cost=250.0,
            roof_size=1200.0,
            average_daily_sunlight=6.0,
            interested_in_installation=True,
        )
        est = calculate_savings(customer)
        result = qualify_lead(customer, est)
        assert result.priority_level == "High"
        assert result.is_qualified is True
        assert result.qualification_score >= 80

    def test_low_priority(self):
        customer = make_customer(
            monthly_electricity_cost=50.0,
            roof_size=300.0,
            average_daily_sunlight=3.0,
            interested_in_installation=False,
        )
        est = calculate_savings(customer)
        result = qualify_lead(customer, est)
        assert result.priority_level == "Low"
        assert result.is_qualified is False

    def test_interest_adds_30_points(self):
        base = make_customer(interested_in_installation=False)
        interested = make_customer(interested_in_installation=True)
        est_base = calculate_savings(base)
        est_interested = calculate_savings(interested)
        score_diff = (
            qualify_lead(interested, est_interested).qualification_score
            - qualify_lead(base, est_base).qualification_score
        )
        assert score_diff == 30

    def test_score_in_valid_range(self):
        customer = make_customer()
        est = calculate_savings(customer)
        result = qualify_lead(customer, est)
        assert 0 <= result.qualification_score <= 100

    def test_notes_populated_for_high_value_customer(self):
        customer = make_customer(
            monthly_electricity_cost=300.0,
            roof_size=1500.0,
            average_daily_sunlight=6.0,
        )
        est = calculate_savings(customer)
        result = qualify_lead(customer, est)
        assert len(result.notes) > 0
