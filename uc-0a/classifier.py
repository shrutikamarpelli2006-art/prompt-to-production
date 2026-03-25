"""
UC-0A — Complaint Classifier
Built directly from agents.md (RICE framework) and skills.md (skill contracts).
Rule-based — no external API required.

skills implemented:
  - classify_complaint : one complaint row in → category + priority + reason + flag out
  - batch_classify     : reads input CSV, applies classify_complaint per row, writes output CSV
"""
import argparse
import csv
import os

# ---------------------------------------------------------------------------
# Enforcement constants — driven by agents.md enforcement rules
# ---------------------------------------------------------------------------

# Rule 1 — valid taxonomy (exact strings only)
VALID_CATEGORIES = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise",
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other",
]

# Rule 2 — severity keywords that must trigger Urgent priority
SEVERITY_KEYWORDS = {
    "injury", "child", "school", "hospital", "ambulance",
    "fire", "hazard", "fell", "collapse",
}

# Category keyword map — ordered by specificity; first match wins
CATEGORY_KEYWORDS = {
    "Pothole":        ["pothole", "pot hole", "crater", "hole in road"],
    "Flooding":       ["flood", "waterlog", "water logging", "inundated", "submerged", "overflow"],
    "Streetlight":    ["streetlight", "street light", "lamp", "light not working", "dark street", "no light"],
    "Waste":          ["garbage", "waste", "trash", "litter", "dump", "rubbish", "bins", "overflowing bin"],
    "Noise":          ["noise", "loud", "sound", "music", "honking", "disturbance", "party"],
    "Road Damage":    ["road damage", "broken road", "road crack", "pavement", "tar", "asphalt", "speed bump"],
    "Heritage Damage":["heritage", "monument", "historical", "old building", "ancient", "protected site"],
    "Heat Hazard":    ["heat", "temperature", "hot", "sun", "shade", "cooling", "humid"],
    "Drain Blockage": ["drain", "sewer", "blockage", "blocked", "clog", "pipe", "sewage", "gutter"],
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _detect_category(description: str) -> str:
    """Match description against category keywords. Returns matched category or 'Other'."""
    desc_lower = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            return category
    return "Other"


def _detect_priority(description: str) -> str:
    """Return 'Urgent' if any severity keyword present, else 'Standard'."""
    desc_lower = description.lower()
    if any(kw in desc_lower for kw in SEVERITY_KEYWORDS):
        return "Urgent"
    return "Standard"


def _build_reason(description: str, category: str, priority: str) -> str:
    """Build a one-sentence reason citing words from the description."""
    desc_lower = description.lower()

    # Find the matched category keyword(s)
    matched_cat_kws = []
    if category != "Other":
        for kw in CATEGORY_KEYWORDS.get(category, []):
            if kw in desc_lower:
                matched_cat_kws.append(f"'{kw}'")

    # Find the matched severity keyword(s)
    matched_sev_kws = []
    for kw in SEVERITY_KEYWORDS:
        if kw in desc_lower:
            matched_sev_kws.append(f"'{kw}'")

    cat_part = f"categorized as '{category}' due to keyword(s) {', '.join(matched_cat_kws)}" \
               if matched_cat_kws else f"categorized as '{category}' (no specific keyword matched)"

    sev_part = f"; priority set to '{priority}' because description contains {', '.join(matched_sev_kws)}" \
               if matched_sev_kws else f"; priority set to '{priority}'"

    return f"Complaint {cat_part}{sev_part}."


# ---------------------------------------------------------------------------
# Skill: classify_complaint
# (from skills.md — one complaint row in → category + priority + reason + flag out)
# ---------------------------------------------------------------------------

def classify_complaint(row: dict) -> dict:
    """
    Skill: classify_complaint
    Input:  dict — a single complaint row with at least a 'description' field.
    Output: dict — with exact keys: category, priority, reason, flag.
    Error:  Genuinely ambiguous or unclassifiable complaints return
            category='Other' and flag='NEEDS_REVIEW'.
    """
    description = str(row.get("description", "")).strip()
    complaint_id = row.get("complaint_id", "")

    # Guard: missing / empty description (agents.md — context rule)
    if not description:
        return {
            "complaint_id": complaint_id,
            "category": "Other",
            "priority": "Low",
            "reason": "No description provided.",
            "flag": "NEEDS_REVIEW",
        }

    category = _detect_category(description)
    priority = _detect_priority(description)
    reason   = _build_reason(description, category, priority)

    # Rule 4 — flag genuinely ambiguous complaints
    flag = "NEEDS_REVIEW" if category == "Other" else ""

    return {
        "complaint_id": complaint_id,
        "category":     category,
        "priority":     priority,
        "reason":       reason,
        "flag":         flag,
    }


# ---------------------------------------------------------------------------
# Skill: batch_classify
# (from skills.md — reads input CSV, applies classify_complaint per row,
#  writes output CSV; must not crash on bad rows; flags nulls)
# ---------------------------------------------------------------------------

def batch_classify(input_path: str, output_path: str) -> None:
    """
    Skill: batch_classify
    Input:  input_path  — path to test_[city].csv
            output_path — path to write results CSV
    Output: CSV file written to output_path with columns:
            complaint_id, category, priority, reason, flag
    Error:  Flags nulls; does not crash on bad rows;
            output is produced even if some rows fail.
    """
    results = []

    with open(input_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Processing {len(rows)} complaint(s) from '{input_path}' ...")

    for i, row in enumerate(rows, 1):
        complaint_id = row.get("complaint_id", f"row_{i}")
        try:
            classified = classify_complaint(row)
        except Exception as exc:
            # Do not crash — log and produce flagged fallback row
            print(f"  [ERROR] row {i} (id={complaint_id}): {exc}")
            classified = {
                "complaint_id": complaint_id,
                "category":     "Other",
                "priority":     "Standard",
                "reason":       f"Classification error: {str(exc)[:120]}",
                "flag":         "NEEDS_REVIEW",
            }

        flag_display = f" [{classified['flag']}]" if classified["flag"] else ""
        print(
            f"  [{i}/{len(rows)}] id={classified['complaint_id']} -> "
            f"{classified['category']} / {classified['priority']}{flag_display}"
        )
        results.append(classified)

    fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    print(f"\nDone. Results written to {output_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        print("UC-0A Complaint Classifier")
        print()
        print("Usage:")
        print("  python classifier.py --input <path_to_csv> --output <results_csv>")
        print()
        print("Examples:")
        print("  python classifier.py --input ..\\data\\city-test-files\\test_pune.csv --output results_pune.csv")
        print("  python classifier.py --input ..\\data\\city-test-files\\test_hyderabad.csv --output results_hyderabad.csv")
        print("  python classifier.py --input ..\\data\\city-test-files\\test_kolkata.csv --output results_kolkata.csv")
        sys.exit(0)

    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
