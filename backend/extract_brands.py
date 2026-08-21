import csv
import json
import re
import os

input_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Unihack_ Sample Dataset - Input.csv")
output_file = os.path.join(os.path.dirname(__file__), "local_brands.json")

brands = []
seen = set()

with open(input_file, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        manuf = row.get("Part_Manuf", "").strip()
        if manuf and manuf not in seen and not (manuf.startswith("--") and manuf.endswith("--")):
            seen.add(manuf)
            # Try to extract code in parentheses
            match = re.match(r'^(.*?)\s*\((.*?)\)$', manuf)
            if match:
                name = match.group(1).strip()
                code = match.group(2).strip()
            else:
                name = manuf
                code = ""
            
            brands.append({
                "original": manuf,
                "MANUFACTURER_NAME": name,
                "MANUFACTURER_CODE": code,
                "BRAND_NAME": name,
                "BRAND_CODE": code
            })

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(brands, f, indent=2)

print(f"Extracted {len(brands)} brands.")
