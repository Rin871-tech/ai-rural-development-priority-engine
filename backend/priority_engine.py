WEIGHTS = {
    "severity": 0.25,
    "population": 0.20,
    "economic": 0.20,
    "health_env": 0.15,
    "delay": 0.10,
    "scheme_gap": 0.10
}

def calculate_priority_with_breakdown(row):
    breakdown = {}

    breakdown["severity"] = round(
        row["severity_score"] * WEIGHTS["severity"], 2
    )

    breakdown["population"] = round(
        (row["population_affected"] / 200000) * WEIGHTS["population"] * 10, 2
    )

    breakdown["economic"] = round(
        row["economic_impact_score"] * WEIGHTS["economic"], 2
    )

    breakdown["health_env"] = round(
        row["health_environment_risk"] * WEIGHTS["health_env"], 2
    )

    breakdown["delay"] = round(
        (row["delay_cost_months"] / 6) * WEIGHTS["delay"] * 10, 2
    )

    breakdown["scheme_gap"] = round(
        (row["scheme_coverage_gap_pct"] / 100) * WEIGHTS["scheme_gap"] * 10, 2
    )

    total_score = round(sum(breakdown.values()), 2)

    return total_score, breakdown
