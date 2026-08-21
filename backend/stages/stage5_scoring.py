def calculate_confidence(row: dict) -> dict:
    """Stage 5: Confidence scoring.
    Combine signals into one score per field.
    """
    meta = row.get("_meta", {})
    
    # Simple scoring logic for prototype
    # Base score is 1.0 (100%)
    score = 1.0
    
    if meta.get("manufacturer_brand_mismatch"):
        score -= 0.3
        
    if meta.get("needs_human_review"):
        score -= 0.4
        
    if not meta.get("source_url_used"):
        score -= 0.2
        
    # Ensure score doesn't go below 0
    score = max(0.0, score)
    
    meta["confidence_score"] = round(score, 2)
    
    # If overall score < 0.6, flag it for human review if not already flagged
    if score < 0.6 and not meta.get("needs_human_review"):
        meta["needs_human_review"] = True
        if not isinstance(meta.get("review_reason"), list):
            meta["review_reason"] = []
        meta["review_reason"].append("Low confidence score")
        
    row["_meta"] = meta
    return row
