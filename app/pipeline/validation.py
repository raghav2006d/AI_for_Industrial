from typing import List, Dict, Any


def validate(fields: Dict[str, str], numeric: Dict[str, float], emissions: Dict[str, Any]) -> List[Dict[str, Any]]:
    flags: List[Dict[str, Any]] = []

    if "DATE" not in fields:
        flags.append({"severity": "warning", "message": "Missing invoice date", "field": "DATE"})

    if numeric.get("kwh", 0.0) < 0:
        flags.append({"severity": "error", "message": "kWh cannot be negative", "field": "KWH"})

    if numeric.get("cost", 0.0) < 0:
        flags.append({"severity": "error", "message": "Cost cannot be negative", "field": "COST"})

    kwh = numeric.get("kwh", 0.0)
    cost = numeric.get("cost", 0.0)
    if kwh > 0 and cost > 0:
        cpk = cost / kwh
        if not (0.01 <= cpk <= 1.0):
            flags.append({
                "severity": "warning",
                "message": f"Cost per kWh ({cpk:.3f}) outside expected range [0.01, 1.00]",
                "field": "COST,KWH",
                "value": cpk,
            })

    if emissions.get("scope2_location_based_kg", 0.0) == 0.0 and kwh > 0:
        flags.append({"severity": "warning", "message": "Emissions computed as zero despite kWh present", "field": "EMISSIONS"})

    return flags