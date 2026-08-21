import os
import csv
import json
import time
import pandas as pd
import google.generativeai as genai
from typing import Dict, Any, List

# Load API key from environment variable
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY environment variable not set. Please set it before running.")

if api_key:
    genai.configure(api_key=api_key)

# ==========================================
# TOOL IMPLEMENTATIONS (Placeholders)
# ==========================================
# In a real scenario, you would load your DataFrames here:
# df_brands = pd.read_csv("UniCat_Manufacturer_and_Brand_List.csv")
# df_lov = pd.read_csv("Unicat_Lov_v1_0_Updated_With_Remarks.csv")
# df_uom = pd.read_csv("Unilog_Master_UOM_Standards_Abbreviations_and_Terms.csv")
# df_frac = pd.read_csv("Decimal_Fraction.csv")

def lookup_manufacturer_brand(query: str) -> Dict[str, str]:
    """
    Fuzzy-match a raw supplier string to the approved UniCat_Manufacturer_and_Brand_List.
    """
    print(f"[TOOL CALL] lookup_manufacturer_brand(query='{query}')")
    # TODO: Implement fuzzy matching against df_brands
    # Mock response for testing:
    return {
        "manufacturer_name": "Rheem Manufacturing",
        "manufacturer_code": "RHEEM",
        "brand_name": "FRIGIDAIRE®",
        "brand_code": "FRIGIDAIRE"
    }

def lookup_lov(classpath: str, attribute_label: str = None) -> List[Dict[str, str]]:
    """
    Return the permitted attribute labels + values for that leaf category.
    """
    print(f"[TOOL CALL] lookup_lov(classpath='{classpath}', attribute_label='{attribute_label}')")
    # TODO: Implement filtering against df_lov
    return [{"label": "Series", "value": "Professional Series"}]

def lookup_uom(raw_unit: str) -> str:
    """
    Normalize a raw unit token to the single approved abbreviation.
    """
    print(f"[TOOL CALL] lookup_uom(raw_unit='{raw_unit}')")
    # TODO: Implement lookup against df_uom
    mapping = {"inches": "in", "IN.": "in", "inch": "in", "amps": "A", "volts": "V"}
    return mapping.get(raw_unit, raw_unit)

def lookup_fraction(decimal_val: float) -> str:
    """
    Convert a decimal remainder to its exact architectural fraction.
    """
    print(f"[TOOL CALL] lookup_fraction(decimal_val={decimal_val})")
    # TODO: Implement lookup against df_frac
    if decimal_val == 0.25: return "1/4"
    if decimal_val == 0.5: return "1/2"
    return str(decimal_val)

def fetch_manufacturer_source(mfg_part_num: str, manufacturer_name: str) -> Dict[str, str]:
    """
    Retrieve the manufacturer's own product page / spec sheet.
    """
    print(f"[TOOL CALL] fetch_manufacturer_source(mfg_part_num='{mfg_part_num}', manufacturer_name='{manufacturer_name}')")
    # TODO: Implement web search or PDF extraction restricted to manufacturer domains
    return {
        "url": "https://www.frigidaire.com/en/p/owner-center/product-support/PDSH4816AF",
        "content": "Professional Series Dishwasher with CleanBoost. 120V 15A. Depth: 50.25 inches. Stainless Steel."
    }

# Map tools for Gemini API
tools_list = [
    lookup_manufacturer_brand,
    lookup_lov,
    lookup_uom,
    lookup_fraction,
    fetch_manufacturer_source
]

# ==========================================
# AGENT ORCHESTRATOR
# ==========================================

def load_system_prompt(filepath="system_prompt.md"):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def process_row(model, row: dict) -> dict:
    """Send a single row to the Gemini model and handle tool calls."""
    input_text = json.dumps(row)
    print(f"\nProcessing item: {row.get('Mfg_Part_Num', 'Unknown')}")
    
    # Start a chat session to handle tool calls automatically
    # (Setting enable_automatic_function_calling=True makes the SDK call our python functions and send the results back)
    chat = model.start_chat(enable_automatic_function_calling=True)
    
    try:
        response = chat.send_message(f"Enrich this item:\n{input_text}")
        
        # Parse the final JSON response from the model
        response_text = response.text
        # Strip markdown json blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        enriched_data = json.loads(response_text)
        return enriched_data
        
    except Exception as e:
        print(f"Error processing row: {e}")
        return {"_meta": {"needs_human_review": True, "review_reason": f"API Error: {str(e)}"}}

def main():
    if not api_key:
        print("Exiting: No API key.")
        return

    system_prompt = load_system_prompt()
    
    model = genai.GenerativeModel(
        model_name="gemini-3.6-flash", # Use the appropriate model
        system_instruction=system_prompt,
        tools=tools_list,
        generation_config={"response_mime_type": "application/json"}
    )
    
    input_csv = "Unihack_ Sample Dataset - Input.csv"
    output_csv = "Unihack_ Enriched_Output.csv"
    
    # Read output schema columns to ensure correct ordering
    schema_file = "Unihack_ Expected Output - Delivery Format.csv"
    if os.path.exists(schema_file):
        with open(schema_file, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader)
    else:
        # Fallback to a basic list if schema file is missing
        headers = ["Mfg_Part_Num", "MANUFACTURER_NAME", "BRAND_NAME", "INVOICE_DESC"] 

    results = []
    
    # Read input data
    with open(input_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            # For demonstration, only process first 3 rows
            if i >= 3: 
                break
                
            enriched = process_row(model, row)
            
            # The model might nest the data inside a 'delivery_format' key or similar, 
            # but our prompt says "Return one JSON object per item with: Every column... as a key"
            if "_meta" in enriched:
                meta = enriched.pop("_meta")
                print(f"Meta: {meta}")
            
            # Ensure all headers exist in the output dictionary
            out_row = {col: enriched.get(col, "") for col in headers}
            results.append(out_row)
            
            time.sleep(2) # Basic rate limiting

    # Write output to CSV
    if results:
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(results)
        print(f"\nProcessing complete! Enriched {len(results)} items. Saved to {output_csv}.")

if __name__ == "__main__":
    main()
