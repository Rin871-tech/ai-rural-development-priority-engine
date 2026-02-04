def explain_decision(row, scheme_gap_pct):
    # Safe reads from your CSV columns
    problem = row.get("problem_type", "Unknown Problem")

    severity = row.get("severity_score", None)
    population = row.get("population_affected", None)
    economic = row.get("economic_impact_score", None)
    health_env = row.get("health_environment_risk", None)
    delay = row.get("delay_cost_months", None)

    # Build clean explanation
    parts = [f"The problem '{problem}' ranks high due to:"]

    if severity is not None:
        parts.append(f"• High severity score ({int(severity)}/10)")
    if population is not None:
        parts.append(f"• Large affected population (~{int(population):,} people)")
    if economic is not None:
        parts.append(f"• Significant economic impact ({int(economic)}/10)")
    if health_env is not None:
        parts.append(f"• Health/environment risk ({int(health_env)}/10)")
    if delay is not None:
        parts.append(f"• Delay cost ({int(delay)} months)")

    if scheme_gap_pct is not None:
        parts.append(f"• Scheme coverage gap ({float(scheme_gap_pct):.1f}%)")

    return " ".join(parts)
