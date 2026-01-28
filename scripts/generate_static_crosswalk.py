#!/usr/bin/env python3
"""Generate static crosswalk data for GitHub Pages."""
import json
import re
from pathlib import Path

def parse_institutions(text):
    if not text or not text.strip():
        return []
    entries = []
    text = re.sub(r'\s+', ' ', text.strip())
    parts = re.split(r'\s*\|\s*|\s{2,}(?=[A-Z])', text)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        match = re.match(r'^([^–\-]+?)(?:\s*[–\-]\s*(.+))?$', part)
        if match:
            name = match.group(1).strip()
            program = match.group(2).strip() if match.group(2) else None
            degree_type = None
            if program:
                degree_match = re.search(r'\b(A\.?A\.?S\.?|A\.?A\.?|A\.?S\.?|B\.?S\.?|B\.?A\.?|B\.?F\.?A\.?|M\.?S\.?|Certificate|LDC|AoC)\b', program, re.IGNORECASE)
                if degree_match:
                    degree_type = degree_match.group(1).upper().replace('.', '')
            if name:
                entries.append({"name": name, "program": program, "degree_type": degree_type, "ircs": None, "key_features": None})
    return entries

def parse_ircs(text):
    if not text or not text.strip():
        return []
    text = re.sub(r'\s+', ' ', text.strip())
    if ';' in text:
        ircs = [irc.strip() for irc in text.split(';') if irc.strip()]
    elif ',' in text and len(text) < 200:
        ircs = [irc.strip() for irc in text.split(',') if irc.strip()]
    else:
        ircs = [text]
    return ircs[:10]

def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    input_file = project_root / "data" / "processed" / "crosswalk_v301.json"
    output_file = project_root / "frontend" / "static" / "crosswalk-data.json"

    with open(input_file) as f:
        data = json.load(f)

    grouped = []
    for cluster in data.get("clusters", []):
        cluster_group = {"cluster_code": cluster["code"], "cluster_name": cluster["name"], "hs_programs": []}
        for program in cluster.get("programs", []):
            hs_program = {
                "name": program["hs_program"],
                "ircs": parse_ircs(program.get("ircs", "")),
                "community_colleges": parse_institutions(program.get("community_college", "")),
                "universities": parse_institutions(program.get("four_year", "")),
                "other": None
            }
            cluster_group["hs_programs"].append(hs_program)
        grouped.append(cluster_group)

    total = sum(len(p["community_colleges"]) + len(p["universities"]) for c in grouped for p in c["hs_programs"])
    institutions = set()
    cc_count = uni_count = 0
    for c in grouped:
        for p in c["hs_programs"]:
            cc_count += len(p["community_colleges"])
            uni_count += len(p["universities"])
            for cc in p["community_colleges"]:
                institutions.add(cc["name"])
            for uni in p["universities"]:
                institutions.add(uni["name"])

    output = {
        "version": data.get("version", "3.01"),
        "source": "Postsecondary Crosswalk3 01.2026.pdf",
        "stats": {"total": total, "unique_institutions": len(institutions), "by_institution_type": {"Community College": cc_count, "University": uni_count}},
        "data": grouped
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"Generated: {output_file}")

if __name__ == "__main__":
    main()
