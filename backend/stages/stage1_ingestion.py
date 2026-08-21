def ingest_and_normalize(raw_row: dict) -> dict:
    """Stage 1: Ingestion & normalization.
    Parse the sparse input row. Normalize whitespace, casing, etc.
    """
    normalized = {}
    placeholders = {'-- unbranded --', '-- no unilog brand --', '-- no dib brand --', 'n/a', ''}
    
    for key, value in raw_row.items():
        if not isinstance(value, str):
            normalized[key] = value
            continue
            
        val_clean = value.strip()
        # Handle placeholders
        is_placeholder = val_clean.lower() in placeholders or (val_clean.startswith('-- ') and val_clean.endswith(' --'))
        if is_placeholder:
            normalized[key] = ""
        else:
            normalized[key] = val_clean
            
    # Add a meta object that will travel with the row
    normalized["_meta"] = {
        "unresolved_fields": [],
        "manufacturer_brand_mismatch": False,
        "source_url_used": "",
        "needs_human_review": False,
        "review_reason": []
    }
    
    return normalized
