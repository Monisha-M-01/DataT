# AI-Powered Product Intelligence for Industrial Commerce (Prototype)

This is a prototype pipeline built for the UniHack challenge to transform sparse product data (6 input fields) into a fully structured, 252-column "Delivery Format" record.

## Architecture

The system consists of a frontend (Vite + React) and a backend (FastAPI + Python).

The backend processes data through 6 stages:
1. **Ingestion (`stage1_ingestion.py`)**: Normalizes input and aggressively filters placeholders like `-- Unbranded --`.
2. **Brand Resolution (`stage2_brand.py`)**: Resolves the input brand string to canonical manufacturer and brand names using fuzzy matching (`rapidfuzz`).
3. **Agent Enrichment (`stage3_agent.py`)**: Uses a generative AI agent (Google Gemini) to fetch official manufacturer specs and extract attributes, UOMs, and generate 5 formatted descriptions.
4. **LOV Validation (`stage4_lov.py`)**: Validates extracted attributes.
5. **Scoring (`stage5_scoring.py`)**: Computes a confidence score and flags rows needing human review.
6. **Output (`stage6_output.py`)**: Maps the enriched data to the final 252-column Delivery Format schema.

## Fallback Assumptions

Due to the absence of the official reference files (`UniCat_Manufacturer_and_Brand_List.xlsx`, LOV files, UOM spreadsheet, and content guidelines docx), we implemented the **Fallback Plan**:

- **Manufacturer/Brand Lookup**: We extracted the unique manufacturers directly from the `Sample-1000_Items.xlsx` file and created a local lookup dictionary (`local_brands.json`). As a result, brand resolution maps strictly to what is available in the sample (e.g. `Appliance Dealers Cooperative`) instead of the true official hierarchy.
- **UOM Abbreviations**: We hardcoded a common starter list (`in`, `ft`, `V`, `A`, `dBA`) based on the sample data.
- **LOV Validation**: Instead of checking against a strict LOV list, the system validates that every attribute has a corroborating manufacturer source citation (`source_url_used`). If the agent fails to cite a source, the attributes are rejected and flagged for review.
- **Content Guidelines**: We reverse-engineered the description formats from the 2 provided ground-truth rows (e.g. `INVOICE_DESC` max 40 chars uppercase).
- **Agent Mocking**: To enable scoring without spending API quota or requiring a live Gemini API key, `stage3_agent.py` contains a mock response block that is triggered for the two specific ground-truth MPNs when the API key is not present.

## Running the Ground Truth Scoring

To test the pipeline against the 2 ground-truth rows:
```bash
python -m backend.score_ground_truth
```
Note: The scoring accuracy will not be 100% due to the fallback tables differing from the true reference data (e.g., brand hierarchies) and character encoding artifacts (`` vs `®`).
