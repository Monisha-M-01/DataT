import csv
import os

def format_output(row: dict) -> dict:
    """Stage 6: Delivery format output.
    Assemble the 252-column row.
    """
    # We will read the headers from the Expected Output file
    schema_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Unihack_ Expected Output - Delivery Format.csv")
    
    headers = [
        "Mfg_Part_Num", "MANUFACTURER_NAME", "BRAND_NAME", "INVOICE_DESC",
        "MOBILE_DESC", "SHORT_DESC", "LONG_DESC1", "RETAIL_DESC", 
        "MARKETING_DESCRIPTION", "Classpath"
    ]
    
    try:
        if os.path.exists(schema_file):
            with open(schema_file, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                headers = next(reader)
    except Exception:
        pass
        
    output_row = {}
    for col in headers:
        output_row[col] = row.get(col, "")
        
    # Ensure all _meta fields are strings so they don't break json dumps if needed
    meta = row.get("_meta", {})
    if isinstance(meta.get("review_reason"), list):
        meta["review_reason"] = " | ".join(meta.get("review_reason", []))
    
    return {
        "data": output_row,
        "_meta": meta
    }
