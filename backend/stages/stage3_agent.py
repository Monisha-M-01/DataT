import os
import json
import time
import threading
import random
import hashlib
from google import genai
from google.genai import types
from backend.store import get_cached_item, set_cached_item
from backend.stages.stage3_rules import apply_rules

# Load API keys
api_keys_str = os.environ.get("GEMINI_API_KEYS", "")
api_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]

class KeyManager:
    def __init__(self, keys):
        self.keys = keys
        self.current_index = 0
        self.clients = [genai.Client(api_key=k) for k in keys]
        
    def get_client(self):
        if not self.clients:
            return None
        return self.clients[self.current_index]
        
    def rotate(self):
        if not self.clients:
            return False
        self.current_index = (self.current_index + 1) % len(self.clients)
        # If we loop back to 0, it means all keys might be exhausted for the day
        return self.current_index != 0

key_manager = KeyManager(api_keys)

class RateLimiter:
    def __init__(self, rpm):
        self.interval = 60.0 / rpm
        self.lock = threading.Lock()
        self.last_call = 0.0

    def wait(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_call
            if elapsed < self.interval:
                time.sleep(self.interval - elapsed)
            self.last_call = time.time()

# Free tier is 15 RPM. We use 14 to be safe.
limiter = RateLimiter(14.0)

def search_manufacturer_docs(brand: str, part_number: str) -> dict:
    """Searches manufacturer domains for product specifications."""
    # Mocking external web search with ground truth data for the pilot
    if "PDSH4816AF" in part_number:
        return {
            "url": "https://www.frigidaire.com/en/p/owner-center/product-support/PDSH4816AF",
            "content": "FRIGIDAIRE Professional Series Dishwasher with CleanBoost. Leg Mounting, 5-Wash Cycle. 120V 15A. Depth With Door Open: 50-1/4 inches. Minimum Height 33-7/8 in. Sound Level 47 dBA. Size: 24 in W x 24-1/4 in D. Stainless Steel. 240 kW-hr Annual Energy, 1 to 12 hr Delay Start Hours."
        }
    elif "WDTS7024RZ" in part_number:
        return {
            "url": "https://learnwhirlpool.com/smartsearchresults?searchtext=WDTS7024R",
            "content": "Whirlpool Eco Series WDTS7024RZ Dishwasher, Built-in Mounting. 120V 10A. Sound Level 41 dBA. 33-7/16 in H x 23-7/8 in W x 22-5/8 in D. Depth With Door Open: 50-3/16 inches. Stainless Steel. Load more and run less with our quietest and largest capacity dishwasher. Features: 3rd rack with extra wash action, Adjustable 2nd Rack, Moisture Repellent Silverware Basket, Sensor cycle, Sani Rinse Option, Leak Detection System, Folding Tines, Normal cycle, Triple Wash Spray, Quick Wash Cycle."
        }
    return {"url": "", "content": "No documents found."}

def fetch_doc(url: str) -> str:
    """Fetches text content from a given URL."""
    return "Mock document content..."

def lookup_uom(raw_unit: str) -> str:
    """Looks up the official UOM abbreviation."""
    # Starter table based on the fallback plan
    mapping = {
        "inches": "in", "inch": "in", "IN": "in", "IN.": "in",
        "volts": "V", "VOLTS": "V",
        "amps": "A", "AMPS": "A", "amp": "A",
        "dBA": "dBA", "dba": "dBA", "decibels": "dBA",
        "feet": "ft", "FT": "ft",
        "pounds": "lb", "LBS": "lb", "lbs": "lb",
        "gallons": "gal", "GAL": "gal"
    }
    return mapping.get(raw_unit, raw_unit)

tools_list = [
    search_manufacturer_docs,
    fetch_doc,
    lookup_uom
]

def load_system_prompt():
    prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "system_prompt.md")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print("Error loading system prompt:", e)
        return "You are an enrichment agent."


MOCK_RESPONSES = {
    "PDSH4816AF": {
        "MFR URL": "https://www.frigidaire.com/en/p/owner-center/product-support/PDSH4816AF",
        "Dept": "Appliances", "Class": "Large Appliances", "Fine": "Dishwashers",
        "SKU - MY_PART_NUMBER": "1515863", "MANUFACTURER_PART_NUMBER": "PDSH4816AF",
        "Classpath": "Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers",
        "MOBILE_DESC": "Rheem Manufacturing FRIGIDAIRE, Dishwasher, Professional Series, PDSH4816AF",
        "INVOICE_DESC": "DISHWASHER LEG 5 SST 120V 15A 50-1/4IN",
        "SHORT_DESC": "FRIGIDAIRE® Professional Series PDSH4816AF Dishwasher With CleanBoost™, Leg Mounting, 5-Wash Cycle, Stainless Steel",
        "LONG_DESC1": "FRIGIDAIRE® Dishwasher With CleanBoost™, Professional Series, 5 Wash Cycles, 120 V, 15 A, Leg Mounting, 24 in W x 24-1/4 in D, 50-1/4 in Depth With Door Open, 8-1/2 in Upper Rack, 11-1/4 in Lower Rack Minimum Height, 10-3/8 in Upper Rack, 13-1/4 in Lower Rack Maximum Height, 47 dBA Sound Level, Stainless Steel, Additional Information: 240 kW-hr Annual Energy, 1 to 12 hr Delay Start Hours",
        "RETAIL_DESC": "Professional Series Dishwasher, Leg Mounting, 5-Wash Cycle, Stainless Steel",
        "With": "With CleanBoost™",
        "Standard/Approvals": "ASSE 1006|CEE Tier 2 Qualified|cUL Listed|ENERGY STAR Certified|NSF Certified|UL Listed",
        "Product Name": "Dishwasher",
        "ATTRIBUTE_LABEL 1": "Series", "ATTRIBUTE_VALUE 1": "Professional Series",
        "ATTRIBUTE_LABEL 2": "Model", "ATTRIBUTE_VALUE 2": "",
        "ATTRIBUTE_LABEL 3": "Number of Wash Cycles", "ATTRIBUTE_VALUE 3": "5",
        "ATTRIBUTE_LABEL 4": "Voltage Rating", "ATTRIBUTE_VALUE 4": "120", "ATTRIBUTE_UOM 4": "V",
        "ATTRIBUTE_LABEL 5": "Amperage Rating", "ATTRIBUTE_VALUE 5": "15", "ATTRIBUTE_UOM 5": "A",
        "ATTRIBUTE_LABEL 6": "Mounting Type", "ATTRIBUTE_VALUE 6": "Leg",
        "ATTRIBUTE_LABEL 7": "Plug Type", "ATTRIBUTE_VALUE 7": "",
        "ATTRIBUTE_LABEL 8": "Size", "ATTRIBUTE_VALUE 8": "24 in W x 24-1/4 in D",
        "ATTRIBUTE_LABEL 9": "Depth With Door Open", "ATTRIBUTE_VALUE 9": "50-1/4", "ATTRIBUTE_UOM 9": "in",
        "ATTRIBUTE_LABEL 10": "Minimum Height", "ATTRIBUTE_VALUE 10": "8-1/2 in Upper Rack, 11-1/4 in Lower Rack",
        "ATTRIBUTE_LABEL 11": "Maximum Height", "ATTRIBUTE_VALUE 11": "10-3/8 in Upper Rack, 13-1/4 in Lower Rack",
        "ATTRIBUTE_LABEL 12": "Sound Level", "ATTRIBUTE_VALUE 12": "47", "ATTRIBUTE_UOM 12": "dBA",
        "ATTRIBUTE_LABEL 13": "Material", "ATTRIBUTE_VALUE 13": "Stainless Steel",
        "ATTRIBUTE_LABEL 14": "Color", "ATTRIBUTE_VALUE 14": "",
        "ATTRIBUTE_LABEL 15": "Additional Information", "ATTRIBUTE_VALUE 15": "240 kW-hr Annual Energy, 1 to 12 hr Delay Start Hours",
        "PART_NUMBER": "20887830",
        "Warranty": "1 Year Manufacturer, 1 Year Labor and Parts",
        "Product Image": "FRIGIDAIRE_PDSH4816AF.jpg",
        "Alternate Image 1": "FRIGIDAIRE_PDSH4816AF_1.jpg", "Alternate Image 2": "FRIGIDAIRE_PDSH4816AF_2.jpg",
        "Alternate Image 3": "FRIGIDAIRE_PDSH4816AF_3.jpg", "Alternate Image 4": "FRIGIDAIRE_PDSH4816AF_4.jpg",
        "Specification Sheet": "FRIGIDAIRE_PDSH4816AF_Specification_Sheet.pdf",
        "Actual Image (Yes/No)": "Yes",
        "_meta": {"source_url_used": "https://www.frigidaire.com/en/p/owner-center/product-support/PDSH4816AF"}
    },
    "WDTS7024RZ": {
        "MFR URL": "https://learnwhirlpool.com/smartsearchresults?searchtext=WDTS7024R",
        "Ref URL 1": "https://www.whirlpool.com/content/dam/global/documents/202412/owners-manual-w11323304-revj.pdf",
        "Ref URL 2": "https://www.whirlpool.com/content/dam/global/documents/202406/installation-instructions-w11323304-revG.pdf",
        "Dept": "Appliances", "Class": "Large Appliances", "Fine": "Dishwashers",
        "PART_NUMBER": "25286031",
        "SKU - MY_PART_NUMBER": "1515867", "MANUFACTURER_PART_NUMBER": "WDTS7024RZ",
        "Classpath": "Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers",
        "MOBILE_DESC": "Whirlpool, Dishwasher, Eco Series, WDTS7024RZ, Built-in Mounting",
        "INVOICE_DESC": "DISHWASHER BLTLN SST SST 120V 10A 41DBA",
        "SHORT_DESC": "Whirlpool® Eco Series WDTS7024RZ Dishwasher, Built-in Mounting, Stainless Steel, Stainless Steel",
        "LONG_DESC1": "Whirlpool® Dishwasher, Eco Series, 120 V, 10 A, Built-in Mounting, 33-7/16 in H x 23-7/8 in W x 22-5/8 in D, 50-3/16 in Depth With Door Open, 33-7/16 in Minimum Height, 41 dBA Sound Level, Stainless Steel, Stainless Steel, Additional Information: Folding Tines, Leak Detection System, Moisture Repellent Silverware Basket, Normal Cycle, Quick Wash Cycle, Sani Rinse Option, Sensor Cycle, Triple Wash Spray",
        "RETAIL_DESC": "Eco Series Dishwasher, Built-in Mounting, Stainless Steel, Stainless Steel",
        "MARKETING_DESCRIPTION": "Load more and run less with our quietest and largest capacity dishwasher. A 3rd Rack provides dedicated space for mugs and bowls, while an adjustable 2nd Rack helps fit all the dishes and pans your family piles up.",
        "ITEM_FEATURES_1": "3rd rack with extra wash action", "ITEM_FEATURES_2": "Adjustable 2nd Rack",
        "ITEM_FEATURES_3": "41 dBA", "ITEM_FEATURES_4": "Moisture Repellent Silverware Basket",
        "ITEM_FEATURES_5": "Sensor cycle", "ITEM_FEATURES_6": "Sani Rinse Option",
        "ITEM_FEATURES_7": "Leak Detection System", "ITEM_FEATURES_8": "Folding Tines",
        "ITEM_FEATURES_9": "Normal cycle", "ITEM_FEATURES_10": "Triple Wash Spray",
        "ITEM_FEATURES_11": "Quick Wash Cycle",
        "With": "With Washing 3rd Rack, Water Repellent Silverware Basket",
        "Product Name": "Dishwasher",
        "ATTRIBUTE_LABEL 1": "Series", "ATTRIBUTE_VALUE 1": "Eco Series",
        "ATTRIBUTE_LABEL 2": "Model", "ATTRIBUTE_VALUE 2": "",
        "ATTRIBUTE_LABEL 3": "Number of Wash Cycles", "ATTRIBUTE_VALUE 3": "",
        "ATTRIBUTE_LABEL 4": "Voltage Rating", "ATTRIBUTE_VALUE 4": "120", "ATTRIBUTE_UOM 4": "V",
        "ATTRIBUTE_LABEL 5": "Amperage Rating", "ATTRIBUTE_VALUE 5": "10", "ATTRIBUTE_UOM 5": "A",
        "ATTRIBUTE_LABEL 6": "Mounting Type", "ATTRIBUTE_VALUE 6": "Built-in",
        "ATTRIBUTE_LABEL 7": "Plug Type", "ATTRIBUTE_VALUE 7": "",
        "ATTRIBUTE_LABEL 8": "Size", "ATTRIBUTE_VALUE 8": "33-7/16 in H x 23-7/8 in W x 22-5/8 in D",
        "ATTRIBUTE_LABEL 9": "Depth With Door Open", "ATTRIBUTE_VALUE 9": "50-3/16", "ATTRIBUTE_UOM 9": "in",
        "ATTRIBUTE_LABEL 10": "Minimum Height", "ATTRIBUTE_VALUE 10": "33-7/16", "ATTRIBUTE_UOM 10": "in",
        "ATTRIBUTE_LABEL 11": "Maximum Height", "ATTRIBUTE_VALUE 11": "",
        "ATTRIBUTE_LABEL 12": "Sound Level", "ATTRIBUTE_VALUE 12": "41", "ATTRIBUTE_UOM 12": "dBA",
        "ATTRIBUTE_LABEL 13": "Material", "ATTRIBUTE_VALUE 13": "Stainless Steel",
        "ATTRIBUTE_LABEL 14": "Color", "ATTRIBUTE_VALUE 14": "Stainless Steel",
        "ATTRIBUTE_LABEL 15": "Additional Information", "ATTRIBUTE_VALUE 15": "Folding Tines, Leak Detection System, Moisture Repellent Silverware Basket, Normal Cycle, Quick Wash Cycle, Sani Rinse Option, Sensor Cycle, Triple Wash Spray",
        "Product Image": "Whirlpool_WDTS7024RZ.jpg",
        "Specification Sheet": "Whirlpool_WDTS7024RZ_Specification_Sheet.pdf",
        "Actual Image (Yes/No)": "Yes",
        "_meta": {"source_url_used": "https://learnwhirlpool.com/smartsearchresults?searchtext=WDTS7024R"}
    }
}


def run_enrichment_agent_batch(rows: list) -> list:
    """Stage 3: Enrichment agent using Gemini. Processes a batch of rows."""
    if not rows:
        return []
        
    # We will build the input for the LLM
    batch_input = []
    # Identify rows that need processing vs rows that can't be processed
    processable_rows = []
    results = [None] * len(rows)
    
    for i, row in enumerate(rows):
        if row.get("_meta", {}).get("brand_unresolved"):
            # Skip enrichment for unresolved brands
            results[i] = row
            continue
            
        raw_desc = row.get("Part_Desc", "")
        raw_manuf = row.get("Part_Manuf", "")
        mpn = row.get("Mfg_Part_Num", "")
        item_hash = hashlib.md5(f"{raw_manuf}|{raw_desc}|{mpn}".encode("utf-8")).hexdigest()
        
        cached = get_cached_item(item_hash)
        if cached:
            results[i] = cached
            continue
            
# -- MOCK LOGIC OVERRIDE --
        if os.environ.get("USE_MOCK_AGENT", "false").lower() == "true":
            if mpn in MOCK_RESPONSES:
                mock_data = MOCK_RESPONSES[mpn].copy()
                new_meta = mock_data.pop("_meta", {})
                row.update(mock_data)
                row.setdefault("_meta", {})
                row["_meta"]["source_url_used"] = new_meta.get("source_url_used", "")
                row["_meta"]["source_used"] = "Mock"
                results[i] = row
                set_cached_item(item_hash, row)
                continue
                
        rules_extracted = apply_rules(row)
        if len(rules_extracted) >= 2:
            row.update(rules_extracted)
            row.setdefault("_meta", {})
            row["_meta"]["source_used"] = "Rules"
            results[i] = row
            set_cached_item(item_hash, row)
            continue
            
        # Temporarily assign a batch_id so we can map it back
        row_copy = row.copy()
        row_copy["_batch_id"] = i
        batch_input.append(row_copy)
        processable_rows.append(i)
        
    if not batch_input:
        return results

    if not key_manager.keys:
        for i in processable_rows:
            row = rows[i]
            row.setdefault("_meta", {})
            row["_meta"]["needs_human_review"] = True
            row["_meta"].setdefault("review_reason", []).append("No Gemini API key found, skipping enrichment.")
            results[i] = row
        return results
        
    system_prompt = load_system_prompt()
    input_text = json.dumps(batch_input)
    
    try:
        max_retries = 3
        retry_count = 0
        response = None
        
        while retry_count <= max_retries:
            try:
                client = key_manager.get_client()
                if not client:
                    raise Exception("Gemini client not initialized")
                    
                limiter.wait()
                chat = client.chats.create(
                    model="gemini-3.6-flash",
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        tools=tools_list,
                        response_mime_type="application/json",
                    )
                )
                response = chat.send_message(f"Enrich this batch:\n{input_text}")
                break
            except Exception as inner_e:
                error_msg = str(inner_e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                    # Rotate key
                    rotated = key_manager.rotate()
                    if rotated:
                        print(f"Key exhausted. Rotated to key {key_manager.current_index}")
                        retry_count = 0 # reset retry count for new key
                        continue
                        
                    retry_count += 1
                    if retry_count > max_retries:
                        for i in processable_rows:
                            row = rows[i]
                            row.setdefault("_meta", {})
                            row["_meta"]["quota_exhausted"] = True
                            row["_meta"]["needs_human_review"] = True
                            row["_meta"].setdefault("review_reason", []).append("Quota exhausted across all keys after max retries")
                            results[i] = row
                        return results # Return early, skipping further processing
                    
                    # Exponential backoff with jitter
                    backoff = (2 ** retry_count) + random.uniform(0, 1)
                    time.sleep(backoff)
                else:
                    raise inner_e
                    
        response_text = response.text
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        enriched_batch = json.loads(response_text)
        if not isinstance(enriched_batch, list):
            enriched_batch = [enriched_batch]
            
        # Map enriched data back by _batch_id
        enriched_dict = {item.get("_batch_id"): item for item in enriched_batch if isinstance(item, dict) and "_batch_id" in item}
        
        for i in processable_rows:
            row = rows[i]
            enriched_data = enriched_dict.get(i)
            
            if enriched_data:
                # Remove _batch_id before merging
                enriched_data.pop("_batch_id", None)
                
                # Merge new meta if present
                if "_meta" in enriched_data:
                    new_meta = enriched_data.pop("_meta")
                    row.setdefault("_meta", {})
                    if new_meta.get("needs_human_review"):
                        row["_meta"]["needs_human_review"] = True
                        row["_meta"].setdefault("review_reason", []).append(new_meta.get("review_reason", ""))
                    
                    row["_meta"]["source_url_used"] = new_meta.get("source_url_used", "")
                    if "unresolved_fields" in new_meta:
                        row["_meta"].setdefault("unresolved_fields", []).extend(new_meta["unresolved_fields"])
                
                row.update(enriched_data)
                
                row.setdefault("_meta", {})
                row["_meta"]["source_used"] = "LLM"
                
                raw_desc = row.get("Part_Desc", "")
                raw_manuf = row.get("Part_Manuf", "")
                mpn = row.get("Mfg_Part_Num", "")
                item_hash = hashlib.md5(f"{raw_manuf}|{raw_desc}|{mpn}".encode("utf-8")).hexdigest()
                set_cached_item(item_hash, row)
            else:
                # Item was dropped by LLM
                row.setdefault("_meta", {})
                row["_meta"]["needs_human_review"] = True
                row["_meta"].setdefault("review_reason", []).append("Agent dropped this item during batch processing")
                
            results[i] = row
            
    except Exception as e:
        for i in processable_rows:
            row = rows[i]
            row.setdefault("_meta", {})
            row["_meta"]["needs_human_review"] = True
            row["_meta"].setdefault("review_reason", []).append(f"Agent Batch Error: {str(e)}")
            results[i] = row
            
    return results
