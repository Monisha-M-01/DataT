def validate_lovs(row: dict) -> dict:
    """Stage 4: LOV Validation (Fallback Mode).
    Since we don't have the LOV file, we validate by ensuring the agent 
    found corroborating evidence (i.e. source_url_used is set).
    """
    meta = row.get("_meta", {})
    source_url = meta.get("source_url_used", "")
    
    # If there is no source URL, we cannot trust the extracted attributes.
    if not source_url:
        meta["needs_human_review"] = True
        if "No manufacturer source confirms these values" not in meta.get("review_reason", []):
            meta.setdefault("review_reason", []).append("No manufacturer source confirms these values.")
            
        # Reject the attributes (clear them out) since they couldn't be validated
        for key in list(row.keys()):
            if key.startswith("ATTRIBUTE_") or key.startswith("ITEM_FEATURES_"):
                row[key] = ""
                
    row["_meta"] = meta
    return row
