from typing import Dict, Any

# Example: location-based electricity factor (kg CO2e per kWh)
DEFAULT_ELECTRICITY_FACTOR = 0.000233  # 0.233 kg/kWh -> 0.000233 metric tons/kWh; we keep kg units here


def compute_emissions(fields: Dict[str, str]) -> Dict[str, Any]:
    kwh_text = fields.get("KWH")
    emissions: Dict[str, Any] = {
        "scope2_location_based_kg": 0.0,
        "factor_source": "demo-default",
        "factor_value_kg_per_kwh": DEFAULT_ELECTRICITY_FACTOR,
    }
    if not kwh_text:
        return emissions
    try:
        kwh = float(str(kwh_text).replace(",", "").strip())
    except Exception:
        return emissions
    emissions["scope2_location_based_kg"] = kwh * DEFAULT_ELECTRICITY_FACTOR
    return emissions