import json
from collections import defaultdict

# Load config from file
with open("config.json") as f:
    CONFIG = json.load(f)

THRESHOLDS = CONFIG.get("classification_thresholds", {
    "State-Official": 100,
    "State-Controlled": 8,
    "State-Linked": 6,
    "State-Aligned": 3
})

CONFIDENCE_RULES = CONFIG.get("confidence_logic", {
    "high": {"min_tech": 1, "min_beh": 1},
    "medium": {"min_tech": 0, "min_beh": 2},
    "low": {"min_tech": 0, "min_beh": 1}
})

TECH_INDICATORS = {item["name"] for item in CONFIG.get("technical_indicators", [])}
BEHAVIORAL_INDICATORS = {item["name"] for item in CONFIG.get("behavioral_indicators", [])}

# Short-circuit rules (hard-coded for now)
SHORT_CIRCUITS = {
    "public affiliation": "State-Official",
    "financial records": "State-Controlled"
}

def classify_channel(indicators):
    score = 0
    tech_count = 0
    beh_count = 0
    applied_short_circuit = None

    for ind in indicators:
        name = ind["subtype"]
        weight = int(ind["weight"])
        group = ind["group_type"]

        score += weight
        if group == "technical":
            tech_count += 1
        elif group == "behavioral":
            beh_count += 1

        if name in SHORT_CIRCUITS:
            applied_short_circuit = SHORT_CIRCUITS[name]

    if applied_short_circuit:
        return {
            "category": applied_short_circuit,
            "confidence": "High",
            "rationale": f"Short-circuit match on '{applied_short_circuit}' via indicator"
        }

    category = "Unclassified"
    for cat, threshold in THRESHOLDS.items():
        if score >= threshold:
            category = cat
            break

    conf = "Low"
    if tech_count >= CONFIDENCE_RULES["high"]["min_tech"] and beh_count >= CONFIDENCE_RULES["high"]["min_beh"]:
        conf = "High"
    elif beh_count >= CONFIDENCE_RULES["medium"]["min_beh"]:
        conf = "Medium"

    rationale = f"Score = {score}; {tech_count} tech, {beh_count} behavioral indicators"

    return {
        "category": category,
        "confidence": conf,
        "rationale": rationale
    }
