# ============================================================================
# ROI Calculator
# Computes financial and sustainability ROI of the optimization system
# ============================================================================
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ROIMetrics:
    """Complete ROI metrics."""
    # Quality improvements
    quality_improvement_pct: float = 0.0
    defect_reduction_pct: float = 0.0
    yield_improvement_pct: float = 0.0
    rework_reduction_pct: float = 0.0

    # Energy & carbon
    energy_reduction_pct: float = 0.0
    energy_savings_kwh: float = 0.0
    carbon_reduction_pct: float = 0.0
    carbon_savings_kg: float = 0.0

    # Financial
    quality_savings_usd: float = 0.0
    energy_savings_usd: float = 0.0
    carbon_credit_value_usd: float = 0.0
    total_annual_savings_usd: float = 0.0
    implementation_cost_usd: float = 0.0
    payback_period_months: float = 0.0
    roi_pct: float = 0.0
    npv_3yr_usd: float = 0.0

    # Operational
    downtime_reduction_pct: float = 0.0
    maintenance_savings_pct: float = 0.0
    batch_time_reduction_pct: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "quality": {
                "improvement_pct": round(self.quality_improvement_pct, 1),
                "defect_reduction_pct": round(self.defect_reduction_pct, 1),
                "yield_improvement_pct": round(self.yield_improvement_pct, 1),
                "rework_reduction_pct": round(self.rework_reduction_pct, 1),
            },
            "energy_carbon": {
                "energy_reduction_pct": round(self.energy_reduction_pct, 1),
                "energy_savings_kwh": round(self.energy_savings_kwh, 1),
                "carbon_reduction_pct": round(self.carbon_reduction_pct, 1),
                "carbon_savings_kg": round(self.carbon_savings_kg, 1),
            },
            "financial": {
                "quality_savings_usd": round(self.quality_savings_usd, 2),
                "energy_savings_usd": round(self.energy_savings_usd, 2),
                "carbon_credit_value_usd": round(self.carbon_credit_value_usd, 2),
                "total_annual_savings_usd": round(self.total_annual_savings_usd, 2),
                "implementation_cost_usd": round(self.implementation_cost_usd, 2),
                "payback_period_months": round(self.payback_period_months, 1),
                "roi_pct": round(self.roi_pct, 1),
                "npv_3yr_usd": round(self.npv_3yr_usd, 2),
            },
            "operational": {
                "downtime_reduction_pct": round(self.downtime_reduction_pct, 1),
                "maintenance_savings_pct": round(self.maintenance_savings_pct, 1),
                "batch_time_reduction_pct": round(self.batch_time_reduction_pct, 1),
            },
        }


class ROICalculator:
    """
    Calculates comprehensive ROI metrics for the manufacturing
    intelligence system.

    Covers:
    1. Quality improvement value (yield, rework, defects)
    2. Energy cost savings
    3. Carbon credit value
    4. Predictive maintenance savings
    5. Overall financial ROI with NPV analysis
    """

    def __init__(self):
        # Industry cost parameters
        self.params = {
            "batch_cost_usd": 5000,          # Cost per batch
            "energy_cost_per_kwh": 0.12,      # Electricity cost
            "carbon_price_per_ton": 50,       # Carbon credit price ($/ton CO2)
            "rework_cost_per_batch": 1500,    # Cost to rework a failed batch
            "reject_cost_per_batch": 3000,    # Cost of a rejected batch
            "annual_batches": 2000,           # Batches per year
            "avg_energy_per_batch_kwh": 50,   # Average energy per batch
            "avg_co2_per_batch_kg": 25,       # Average CO2 per batch
            "baseline_defect_rate": 0.05,     # 5% defect rate
            "baseline_rework_rate": 0.08,     # 8% rework rate
            "implementation_cost_usd": 150000, # System implementation cost
            "annual_maintenance_cost": 20000,  # Annual system maintenance
            "discount_rate": 0.08,            # For NPV calculation
            "maintenance_cost_annual": 100000, # Equipment maintenance budget
            "downtime_cost_per_hour": 5000,   # Cost of unplanned downtime
            "annual_downtime_hours": 200,     # Baseline unplanned downtime
        }

    def calculate_roi(
        self,
        baseline_metrics: Dict,
        optimized_metrics: Dict,
        custom_params: Optional[Dict] = None,
    ) -> ROIMetrics:
        """
        Calculate ROI based on baseline vs optimized performance.

        baseline_metrics: {"avg_hardness", "avg_dissolution", "avg_energy_kwh",
                          "avg_co2_kg", "defect_rate", "rework_rate", ...}
        optimized_metrics: Same structure with optimized values.
        """
        p = self.params.copy()
        if custom_params:
            p.update(custom_params)

        roi = ROIMetrics()

        # === Quality Improvements ===
        baseline_quality = baseline_metrics.get("overall_quality_score", 80)
        optimized_quality = optimized_metrics.get("overall_quality_score", 85)
        roi.quality_improvement_pct = (
            (optimized_quality - baseline_quality) / baseline_quality * 100
        )

        # Defect reduction
        bl_defect = baseline_metrics.get("defect_rate", p["baseline_defect_rate"])
        opt_defect = optimized_metrics.get("defect_rate", bl_defect * 0.6)
        roi.defect_reduction_pct = (
            (bl_defect - opt_defect) / bl_defect * 100
        )

        # Rework reduction
        bl_rework = baseline_metrics.get("rework_rate", p["baseline_rework_rate"])
        opt_rework = optimized_metrics.get("rework_rate", bl_rework * 0.5)
        roi.rework_reduction_pct = (
            (bl_rework - opt_rework) / bl_rework * 100
        )

        # Yield improvement
        roi.yield_improvement_pct = (
            roi.defect_reduction_pct * bl_defect
            + roi.rework_reduction_pct * bl_rework * 0.5
        )

        # === Energy & Carbon ===
        bl_energy = baseline_metrics.get("avg_energy_kwh", p["avg_energy_per_batch_kwh"])
        opt_energy = optimized_metrics.get("avg_energy_kwh", bl_energy * 0.88)
        roi.energy_reduction_pct = (
            (bl_energy - opt_energy) / bl_energy * 100
        )
        roi.energy_savings_kwh = (bl_energy - opt_energy) * p["annual_batches"]

        bl_co2 = baseline_metrics.get("avg_co2_kg", p["avg_co2_per_batch_kg"])
        opt_co2 = optimized_metrics.get("avg_co2_kg", bl_co2 * 0.85)
        roi.carbon_reduction_pct = (bl_co2 - opt_co2) / bl_co2 * 100
        roi.carbon_savings_kg = (bl_co2 - opt_co2) * p["annual_batches"]

        # === Financial Calculations ===
        # Quality savings (reduced defects and rework)
        defect_savings = (
            (bl_defect - opt_defect) * p["annual_batches"]
            * p["reject_cost_per_batch"]
        )
        rework_savings = (
            (bl_rework - opt_rework) * p["annual_batches"]
            * p["rework_cost_per_batch"]
        )
        roi.quality_savings_usd = defect_savings + rework_savings

        # Energy savings
        roi.energy_savings_usd = (
            roi.energy_savings_kwh * p["energy_cost_per_kwh"]
        )

        # Carbon credit value
        roi.carbon_credit_value_usd = (
            roi.carbon_savings_kg / 1000 * p["carbon_price_per_ton"]
        )

        # Maintenance savings (predictive maintenance)
        roi.maintenance_savings_pct = optimized_metrics.get(
            "maintenance_savings_pct", 15
        )
        maintenance_savings = (
            p["maintenance_cost_annual"] * roi.maintenance_savings_pct / 100
        )

        # Downtime reduction
        roi.downtime_reduction_pct = optimized_metrics.get(
            "downtime_reduction_pct", 20
        )
        downtime_savings = (
            p["annual_downtime_hours"] * roi.downtime_reduction_pct / 100
            * p["downtime_cost_per_hour"]
        )

        # Batch time reduction
        roi.batch_time_reduction_pct = optimized_metrics.get(
            "batch_time_reduction_pct", 5
        )

        # Total annual savings
        roi.total_annual_savings_usd = (
            roi.quality_savings_usd
            + roi.energy_savings_usd
            + roi.carbon_credit_value_usd
            + maintenance_savings
            + downtime_savings
        )

        # Implementation cost
        roi.implementation_cost_usd = p["implementation_cost_usd"]

        # Payback period
        if roi.total_annual_savings_usd > 0:
            roi.payback_period_months = (
                roi.implementation_cost_usd / roi.total_annual_savings_usd * 12
            )
        else:
            roi.payback_period_months = float("inf")

        # ROI percentage (1st year)
        net_first_year = (
            roi.total_annual_savings_usd
            - p["annual_maintenance_cost"]
        )
        roi.roi_pct = (
            (net_first_year - roi.implementation_cost_usd)
            / roi.implementation_cost_usd * 100
        )

        # NPV (3-year)
        roi.npv_3yr_usd = self._compute_npv(
            initial_investment=roi.implementation_cost_usd,
            annual_savings=roi.total_annual_savings_usd,
            annual_costs=p["annual_maintenance_cost"],
            discount_rate=p["discount_rate"],
            years=3,
        )

        return roi

    def compute_from_ab_test(
        self, ab_results: Dict, custom_params: Optional[Dict] = None
    ) -> ROIMetrics:
        """
        Compute ROI directly from A/B test results.
        """
        metrics = ab_results.get("metrics", {})

        baseline = {}
        optimized = {}

        # Extract quality metrics
        for metric_name, vals in metrics.items():
            control_mean = vals.get("control_mean", 0)
            treatment_mean = vals.get("treatment_mean", 0)

            if metric_name == "Energy_Consumption_kWh":
                baseline["avg_energy_kwh"] = control_mean
                optimized["avg_energy_kwh"] = treatment_mean
            elif metric_name == "CO2_Emissions_kg":
                baseline["avg_co2_kg"] = control_mean
                optimized["avg_co2_kg"] = treatment_mean
            elif metric_name == "Hardness":
                baseline["avg_hardness"] = control_mean
                optimized["avg_hardness"] = treatment_mean
            elif metric_name == "Dissolution_Rate":
                baseline["avg_dissolution"] = control_mean
                optimized["avg_dissolution"] = treatment_mean

        # Compute quality score
        baseline["overall_quality_score"] = 80
        optimized["overall_quality_score"] = 80 + sum(
            vals.get("improvement_pct", 0) * 0.2
            for vals in metrics.values()
        )

        return self.calculate_roi(baseline, optimized, custom_params)

    def sensitivity_analysis(
        self,
        baseline_metrics: Dict,
        optimized_metrics: Dict,
        variable: str = "energy_cost_per_kwh",
        range_pct: float = 50,
        steps: int = 10,
    ) -> List[Dict]:
        """
        Run sensitivity analysis on a single variable to understand
        how ROI changes with parameter variations.
        """
        base_value = self.params.get(variable, 0)
        if base_value == 0:
            return []

        results = []
        for i in range(steps + 1):
            factor = (1 - range_pct / 100) + (
                2 * range_pct / 100 * i / steps
            )
            test_value = base_value * factor

            custom = {variable: test_value}
            roi = self.calculate_roi(
                baseline_metrics, optimized_metrics, custom
            )

            results.append({
                variable: round(test_value, 4),
                "factor": round(factor, 2),
                "total_annual_savings_usd": round(roi.total_annual_savings_usd, 2),
                "payback_months": round(roi.payback_period_months, 1),
                "roi_pct": round(roi.roi_pct, 1),
                "npv_3yr_usd": round(roi.npv_3yr_usd, 2),
            })

        return results

    def _compute_npv(
        self,
        initial_investment: float,
        annual_savings: float,
        annual_costs: float,
        discount_rate: float,
        years: int,
    ) -> float:
        """Compute Net Present Value."""
        npv = -initial_investment
        net_annual = annual_savings - annual_costs

        for year in range(1, years + 1):
            npv += net_annual / (1 + discount_rate) ** year

        return npv

    def generate_executive_summary(self, roi: ROIMetrics) -> str:
        """Generate executive summary of ROI analysis."""
        return f"""
=== Manufacturing Intelligence System - ROI Executive Summary ===

QUALITY IMPACT:
  - Quality improvement: {roi.quality_improvement_pct:.1f}%
  - Defect reduction: {roi.defect_reduction_pct:.1f}%
  - Rework reduction: {roi.rework_reduction_pct:.1f}%
  - Quality-related savings: ${roi.quality_savings_usd:,.0f}/year

ENERGY & SUSTAINABILITY:
  - Energy reduction: {roi.energy_reduction_pct:.1f}% ({roi.energy_savings_kwh:,.0f} kWh/year)
  - Carbon reduction: {roi.carbon_reduction_pct:.1f}% ({roi.carbon_savings_kg:,.0f} kg CO2/year)
  - Energy cost savings: ${roi.energy_savings_usd:,.0f}/year
  - Carbon credit value: ${roi.carbon_credit_value_usd:,.0f}/year

OPERATIONAL:
  - Downtime reduction: {roi.downtime_reduction_pct:.1f}%
  - Maintenance savings: {roi.maintenance_savings_pct:.1f}%
  - Batch time reduction: {roi.batch_time_reduction_pct:.1f}%

FINANCIAL:
  - Total annual savings: ${roi.total_annual_savings_usd:,.0f}
  - Implementation cost: ${roi.implementation_cost_usd:,.0f}
  - Payback period: {roi.payback_period_months:.1f} months
  - First-year ROI: {roi.roi_pct:.1f}%
  - 3-year NPV: ${roi.npv_3yr_usd:,.0f}
"""
