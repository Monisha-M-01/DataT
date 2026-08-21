# AI-Powered Product Intelligence for Industrial Commerce

An intelligent, multi-stage data enrichment and normalization pipeline. This project transforms raw, unstructured product data (like MPNs and loose descriptions) into clean, standardized, and highly structured "Delivery Format" records.

## Key Features

- **Automated Brand Resolution:** Identifies and standardizes manufacturer and brand names from raw inputs.
- **LLM-Powered Extraction:** Utilizes the Gemini API to parse complex product descriptions and extract precise technical attributes (e.g., Voltage, Mounting Type, Dimensions).
- **Graceful Fallback & Rules Engine:** Built-in resilience. If the LLM API hits rate limits or goes offline, the system seamlessly falls back to a regex-based rules engine to extract baseline data without crashing.
- **Strict Verification Guardrails:** Automatically flags unverified data. If extracted attributes cannot be tied to a trusted manufacturer source URL, the pipeline scrubs the unverified fields and flags the item for human review.
- **Interactive UI Dashboard:** A sleek, React/Vite-based frontend that visualizes the pipeline's output. Includes real-time search, interactive filter metrics, and highlights data confidence scores so you can easily spot rows that need human attention.

## Architecture

The system consists of a frontend (Vite + React) and a backend (FastAPI + Python).

The backend processes data through 6 stages:
1. **Ingestion (`stage1_ingestion.py`)**: Normalizes input and aggressively filters placeholders like `-- Unbranded --`.
2. **Brand Resolution (`stage2_brand.py`)**: Resolves the input brand string to canonical manufacturer and brand names using fuzzy matching (`rapidfuzz`).
3. **Agent Enrichment (`stage3_agent.py`)**: Uses a generative AI agent (Google Gemini) to fetch official manufacturer specs and extract attributes, UOMs, and generate formatted descriptions.
4. **LOV Validation (`stage4_lov.py`)**: Validates extracted attributes.
5. **Scoring (`stage5_scoring.py`)**: Computes a confidence score and flags rows needing human review.
6. **Output (`stage6_output.py`)**: Maps the enriched data to the final 252-column Delivery Format schema.

## Fallback Configurations

Due to the absence of official reference files (Manufacturer and Brand Lists, LOV files, UOM spreadsheets, and content guidelines), the system implements the following fallback strategies:

- **Manufacturer/Brand Lookup**: Extracts unique manufacturers directly from sample items to create a local lookup dictionary (`local_brands.json`).
- **UOM Abbreviations**: Hardcoded a common starter list (`in`, `ft`, `V`, `A`, `dBA`) based on sample data.
- **LOV Validation**: Instead of checking against a strict LOV list, the system validates that every attribute has a corroborating manufacturer source citation (`source_url_used`). If the agent fails to cite a source, the attributes are rejected and flagged for review.
- **Content Guidelines**: Reverse-engineered description formats from ground-truth examples.
- **Agent Mocking**: To enable scoring without spending API quota, `stage3_agent.py` contains a mock response block that is triggered for specific ground-truth MPNs when the API key is not present.

## Running the Ground Truth Scoring

To test the pipeline against the ground-truth rows:
```bash
python -m backend.score_ground_truth
```
Note: The scoring accuracy will not be 100% due to the fallback tables differing from the true reference data (e.g., brand hierarchies) and character encoding artifacts.
