from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from priority_engine import calculate_priority_with_breakdown
from explain import explain_decision

app = FastAPI()

# CORS (Hackathon-safe)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Helpers ----------
def risk_level(score: float) -> str:
    if score >= 8:
        return "HIGH"
    elif score >= 6:
        return "MEDIUM"
    return "LOW"


# ---------- API ----------
@app.get("/districts")
def get_districts():
    df = pd.read_csv("village_data.csv")
    return sorted(df["district"].dropna().unique().tolist())


@app.get("/priorities")
def get_priorities():
    df = pd.read_csv("village_data.csv")
    response = []

    # ensure taluka column exists even if some rows are blank
    if "taluka" not in df.columns:
        df["taluka"] = None

    for _, row in df.iterrows():
        score, breakdown = calculate_priority_with_breakdown(row)
        gap = row.get("scheme_coverage_gap_pct", None)

        response.append({
            "district": row["district"],
            "taluka": None if pd.isna(row["taluka"]) else row["taluka"],
            "problem": row["problem_type"],
            "priority_score": score,
            "risk_level": risk_level(score),
            "scheme_gap": gap,
            "weight_contribution": breakdown,
            "explanation": explain_decision(row, gap)
        })

    return response


@app.get("/district-priority-index")
def district_priority_index():
    df = pd.read_csv("village_data.csv")

    # compute priority score per row
    df["priority_score"] = df.apply(
        lambda row: calculate_priority_with_breakdown(row)[0],
        axis=1
    )

    district_data = []
    for district, group in df.groupby("district"):
        avg_priority = group["priority_score"].mean()
        avg_scheme_gap = group.get("scheme_coverage_gap_pct", pd.Series([0]*len(group))).mean()
        avg_delay = group.get("delay_cost_months", pd.Series([0]*len(group))).mean()

        delay_multiplier = 1 + (avg_delay / 12)
        dpi = round(avg_priority * (1 + avg_scheme_gap / 100) * delay_multiplier, 2)

        district_data.append({
            "district": district,
            "district_priority_index": dpi,
            "risk_band": "HIGH" if dpi >= 12 else ("MEDIUM" if dpi >= 8 else "LOW")
        })

    return sorted(district_data, key=lambda x: x["district_priority_index"], reverse=True)


@app.get("/district/{district_name}/talukas")
def get_talukas(district_name: str):
    df = pd.read_csv("village_data.csv")

    if "taluka" not in df.columns:
        return []

    df = df[df["district"] == district_name]
    return sorted(df["taluka"].dropna().unique().tolist())


@app.get("/district/{district_name}/taluka-budget")
def taluka_budget_split(district_name: str):
    df = pd.read_csv("village_data.csv")

    if "taluka" not in df.columns:
        return []

    df = df[df["district"] == district_name].dropna(subset=["taluka"])

    taluka_scores = []
    for taluka, group in df.groupby("taluka"):
        scores = []
        for _, row in group.iterrows():
            score, _ = calculate_priority_with_breakdown(row)
            scores.append(score)

        avg_score = round((sum(scores) / len(scores)) if scores else 0, 2)
        taluka_scores.append({"taluka": taluka, "avg_priority": avg_score})

    total = sum(t["avg_priority"] for t in taluka_scores) or 1
    district_budget = 1000  # ₹ Crore demo

    for t in taluka_scores:
        t["recommended_budget_crore"] = round((t["avg_priority"] / total) * district_budget, 2)

    return sorted(taluka_scores, key=lambda x: x["recommended_budget_crore"], reverse=True)

@app.get("/taluka/{taluka_name}/priorities")
def taluka_priorities(taluka_name: str):
    df = pd.read_csv("village_data.csv")

    if "taluka" not in df.columns:
        return []

    # normalize taluka names
    df["taluka"] = df["taluka"].astype(str).str.strip()
    taluka_key = taluka_name.strip()

    df = df[df["taluka"] == taluka_key]

    response = []
    for _, row in df.iterrows():
        score, breakdown = calculate_priority_with_breakdown(row)

        gap = float(row.get("scheme_coverage_gap_pct", 0) or 0)
        eligible = int(row.get("population_affected", 0) or 0)
        beneficiaries = int(round(eligible * (1 - gap / 100)))

        if gap >= 50:
            status = "CRITICAL"
        elif gap >= 20:
            status = "UNDERPERFORMING"
        else:
            status = "ON_TRACK"

        response.append({
            "district": row["district"],
            "taluka": taluka_key,
            "problem": row["problem_type"],
            "priority_score": score,
            "risk_level": risk_level(score),

            # ✅ Scheme Intelligence Module output
            "scheme_intelligence": {
                "scheme": row.get("linked_scheme", "Unknown"),
                "eligible_est": eligible,
                "beneficiaries_current": beneficiaries,
                "coverage_gap_pct": gap,
                "status": status
            },

            "weight_contribution": breakdown,
            "explanation": explain_decision(row, gap)
        })

    return sorted(response, key=lambda x: x["priority_score"], reverse=True)


@app.get("/budget-allocation")
def budget_allocation(total_budget_crore: int = 1000):
    df = pd.read_csv("village_data.csv")

    df["priority_score"] = df.apply(
        lambda row: calculate_priority_with_breakdown(row)[0],
        axis=1
    )

    district_scores = {}
    for district, group in df.groupby("district"):
        avg_priority = group["priority_score"].mean()
        avg_scheme_gap = group.get("scheme_coverage_gap_pct", pd.Series([0]*len(group))).mean()
        avg_delay = group.get("delay_cost_months", pd.Series([0]*len(group))).mean()

        delay_multiplier = 1 + (avg_delay / 12)
        dpi = avg_priority * (1 + avg_scheme_gap / 100) * delay_multiplier
        district_scores[district] = dpi

    total_dpi = sum(district_scores.values()) or 1

    allocation = []
    for district, dpi in district_scores.items():
        share = dpi / total_dpi
        allocation.append({
            "district": district,
            "recommended_budget_crore": round(share * total_budget_crore, 2),
            "allocation_reason": "Higher composite rural risk and scheme gap"
        })

    return sorted(allocation, key=lambda x: x["recommended_budget_crore"], reverse=True)
