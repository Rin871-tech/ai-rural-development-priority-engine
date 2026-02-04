SCHEME_MAP = {
    "Water": {
        "scheme": "Jal Jeevan Mission",
        "eligible_households": 4800,
        "beneficiaries": 1900
    },
    "Health": {
        "scheme": "Ayushman Bharat",
        "eligible_households": 3000,
        "beneficiaries": 2100
    }
}

def scheme_gap(problem_type):
    data = SCHEME_MAP.get(problem_type)
    if not data:
        return None
    
    gap = 100 - (data["beneficiaries"] / data["eligible_households"]) * 100
    return round(gap, 1)
