# ============================================================================
# Physics-Informed Models
# Monod kinetics, mass balance, and process physics approximations
# ============================================================================
import numpy as np
from typing import Dict, Tuple, Optional
from scipy.integrate import odeint


class PharmaceuticalProcessPhysics:
    """
    Physics-informed models for pharmaceutical tablet manufacturing.
    Encodes domain knowledge about:
    - Granulation mechanics (binder-particle interaction)
    - Drying kinetics (moisture removal)
    - Compression physics (Heckel equation analogue)
    - Energy consumption models
    """

    def __init__(self):
        # Granulation model parameters
        self.k_granulation = 0.15  # granulation rate constant
        self.binder_efficiency = 0.85

        # Drying model parameters
        self.k_drying = 0.03  # drying rate constant
        self.activation_energy = 30.0  # kJ/mol

        # Compression model parameters (Heckel-like)
        self.heckel_k = 0.05  # material compressibility
        self.heckel_a = 0.3  # initial porosity

        # Energy model parameters
        self.motor_efficiency = 0.85
        self.thermal_efficiency = 0.75

    def granulation_model(
        self, granulation_time: float, binder_amount: float,
        moisture_content_initial: float = 5.0,
    ) -> Dict[str, float]:
        """
        Model granule formation based on binder-substrate interaction.
        Uses modified Avrami equation for granule growth.
        """
        # Effective binder concentration
        c_eff = binder_amount * self.binder_efficiency

        # Granule size growth (Avrami-like)
        t = np.linspace(0, granulation_time, 100)
        growth = 1 - np.exp(-self.k_granulation * c_eff * t ** 1.5)

        # Final granule quality proxy
        granule_quality = growth[-1] * 100

        # Moisture distribution
        moisture_cv = max(0.05, 1.0 - 0.03 * granulation_time)

        # Energy for granulation (motor + mixing)
        energy = (15 + 8 * np.mean(np.sin(np.pi * t / granulation_time))) * granulation_time / 60

        return {
            "granule_quality": float(np.clip(granule_quality, 0, 100)),
            "moisture_cv": float(moisture_cv),
            "granulation_energy_kwh": float(energy),
            "endpoint_reached": bool(growth[-1] > 0.85),
        }

    def drying_kinetics(
        self, drying_temp: float, drying_time: float,
        initial_moisture: float = 3.5,
    ) -> Dict[str, float]:
        """
        Model moisture removal using first-order drying kinetics.
        Arrhenius-adjusted rate constant.
        """
        # Arrhenius rate adjustment
        T_ref = 60.0  # Reference temperature
        R = 8.314e-3  # kJ/(mol·K)
        T_k = drying_temp + 273.15
        T_ref_k = T_ref + 273.15
        k_adj = self.k_drying * np.exp(
            -self.activation_energy / R * (1 / T_k - 1 / T_ref_k)
        )

        # First-order drying
        t = np.linspace(0, drying_time, 100)
        moisture = initial_moisture * np.exp(-k_adj * t)

        # Critical moisture content
        final_moisture = moisture[-1]

        # Energy for drying (heating + blower)
        energy = (35 + 10 * np.exp(-t[-1] / 20)) * drying_time / 60

        # Residual solvent risk
        solvent_risk = float(final_moisture > 3.0)

        return {
            "final_moisture": float(final_moisture),
            "drying_rate": float(k_adj),
            "drying_energy_kwh": float(energy),
            "drying_efficiency": float(
                (initial_moisture - final_moisture) / initial_moisture * 100
            ),
            "solvent_risk": solvent_risk,
        }

    def compression_model(
        self, compression_force: float, machine_speed: float,
        particle_size_proxy: float = 50.0,
    ) -> Dict[str, float]:
        """
        Model tablet compression using modified Heckel equation.
        Relates compression force to tablet density/hardness.
        """
        # Heckel equation: ln(1/(1-D)) = k*P + A
        # where D = relative density, P = pressure, k = compressibility
        P = compression_force * 1000  # Convert kN to Pa (simplified)

        # Relative density
        D = 1 - np.exp(-(self.heckel_k * P / 1000 + self.heckel_a))
        D = np.clip(D, 0.3, 0.99)

        # Hardness prediction (empirical correlation)
        hardness = 50 + 4.0 * compression_force - 0.08 * machine_speed
        hardness = np.clip(hardness, 30, 150)

        # Friability (inverse relationship with density)
        friability = 2.0 * (1 - D)
        friability = np.clip(friability, 0.1, 2.0)

        # Energy per tablet
        energy_per_tablet = compression_force * 0.001 * machine_speed / self.motor_efficiency

        # Ejection force proxy
        ejection_force = compression_force * 0.15 * (1 + 0.01 * machine_speed)

        return {
            "relative_density": float(D),
            "predicted_hardness": float(hardness),
            "predicted_friability": float(friability),
            "energy_per_tablet": float(energy_per_tablet),
            "ejection_force": float(ejection_force),
            "capping_risk": float(D > 0.95),
        }

    def energy_consumption_model(
        self, params: Dict
    ) -> Dict[str, float]:
        """
        Physics-based total energy consumption model.
        Accounts for all process phases.
        """
        gt = params.get("Granulation_Time", 15)
        ba = params.get("Binder_Amount", 8.5)
        dt = params.get("Drying_Temp", 60)
        dry_t = params.get("Drying_Time", 25)
        cf = params.get("Compression_Force", 12.5)
        ms = params.get("Machine_Speed", 150)
        lc = params.get("Lubricant_Conc", 1.0)

        # Phase-level energy estimates
        e_prep = 2.0 * 15 / 60  # kWh
        e_gran = (15 + 8 * 0.5) * gt / 60
        e_dry = (35 * dry_t + 10 * (1 - np.exp(-dry_t / 20)) * dry_t) / 60
        e_mill = (20 + ms / 15) * 20 / 60
        e_blend = (10 + 5 * lc) * 25 / 60
        e_comp = (25 + cf * 2 + ms / 10) * 40 / 60
        e_coat = 18 * 20 / 60
        e_qc = 3 * 10 / 60

        total = e_prep + e_gran + e_dry + e_mill + e_blend + e_comp + e_coat + e_qc

        return {
            "total_energy_kwh": float(total),
            "preparation_kwh": float(e_prep),
            "granulation_kwh": float(e_gran),
            "drying_kwh": float(e_dry),
            "milling_kwh": float(e_mill),
            "blending_kwh": float(e_blend),
            "compression_kwh": float(e_comp),
            "coating_kwh": float(e_coat),
            "qc_kwh": float(e_qc),
            "energy_efficiency": float(
                (e_comp + e_gran) / (total + 1e-10) * 100
            ),
        }

    def predict_all(self, params: Dict) -> Dict[str, float]:
        """Run all physics models and return combined predictions."""
        results = {}

        gran = self.granulation_model(
            params.get("Granulation_Time", 15),
            params.get("Binder_Amount", 8.5),
        )
        results.update({f"physics_{k}": v for k, v in gran.items()})

        dry = self.drying_kinetics(
            params.get("Drying_Temp", 60),
            params.get("Drying_Time", 25),
        )
        results.update({f"physics_{k}": v for k, v in dry.items()})

        comp = self.compression_model(
            params.get("Compression_Force", 12.5),
            params.get("Machine_Speed", 150),
        )
        results.update({f"physics_{k}": v for k, v in comp.items()})

        energy = self.energy_consumption_model(params)
        results.update({f"physics_{k}": v for k, v in energy.items()})

        return results
