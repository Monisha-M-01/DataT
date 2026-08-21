import os
import csv
from backend.stages.stage1_ingestion import ingest_and_normalize
from backend.stages.stage2_brand import resolve_brand
from backend.stages.stage3_agent import run_enrichment_agent_batch
from backend.stages.stage4_lov import validate_lovs
from backend.stages.stage5_scoring import calculate_confidence
from backend.stages.stage6_output import format_output

def score_pipeline():
    ground_truth_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Unihack_ Expected Output - Delivery Format.csv")
    
    if not os.path.exists(ground_truth_file):
        print("Ground truth file not found.")
        return
        
    with open(ground_truth_file, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        ground_truth_rows = list(reader)
        
    print(f"Loaded {len(ground_truth_rows)} ground truth rows for scoring.\n")
    
    total_fields_checked = 0
    total_fields_matched = 0
    char_limit_violations = 0
    
    for i, gt_row in enumerate(ground_truth_rows):
        print(f"--- Scoring Row {i+1} (MPN: {gt_row.get('Mfg_Part_Num')}) ---")
        
        # Build raw input row
        raw_input = {
            "Mfg_Part_Num": gt_row.get("Mfg_Part_Num", ""),
            "Part_Desc": gt_row.get("Part_Desc", ""),
            "E1_Brand": gt_row.get("E1_Brand", ""),
            "Unilog_Brand": gt_row.get("Unilog_Brand", ""),
            "DIB_Brand": gt_row.get("DIB_Brand", ""),
            "Part_Manuf": gt_row.get("Part_Manuf", ""),
        }
        
        # Run pipeline stages
        parsed = ingest_and_normalize(raw_input)
        print("After ingestion:", parsed)
        parsed.update(resolve_brand(parsed))
        enriched_batch = run_enrichment_agent_batch([parsed])
        enriched = enriched_batch[0] if enriched_batch else parsed
        validated = validate_lovs(enriched)
        scored = calculate_confidence(validated)
        final = format_output(scored)
        
        output = final["data"]
        
        # Score fields
        fields_matched = 0
        fields_checked = 0
        
        for key in output:
            if key in raw_input:
                continue # Skip input fields
                
            expected = gt_row.get(key, "").strip()
            actual = output.get(key, "").strip() if output.get(key) else ""
            
            # We only score fields that the ground truth actually filled in
            if expected:
                fields_checked += 1
                if str(expected).lower() == str(actual).lower():
                    fields_matched += 1
                else:
                    print(f"Mismatch in {key}:\n  Expected: '{expected}'\n  Actual:   '{actual}'")
                    
        # Check character limits
        if len(output.get("INVOICE_DESC", "")) > 40:
            print(f"Character limit violation: INVOICE_DESC > 40 chars ({len(output['INVOICE_DESC'])})")
            char_limit_violations += 1
            
        print(f"Row {i+1} Accuracy: {fields_matched}/{fields_checked} ({(fields_matched/fields_checked)*100:.1f}%)")
        print(f"Review Reasons: {final.get('_meta', {}).get('review_reason')}")
        total_fields_matched += fields_matched
        total_fields_checked += fields_checked
        print("\n")
        
    print("=== FINAL SCORE ===")
    if total_fields_checked > 0:
        print(f"Overall Field Accuracy: {(total_fields_matched/total_fields_checked)*100:.1f}% ({total_fields_matched}/{total_fields_checked})")
    print(f"Character Limit Violations: {char_limit_violations}")

if __name__ == "__main__":
    score_pipeline()
