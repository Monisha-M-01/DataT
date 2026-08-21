import re

def apply_rules(row: dict) -> dict:
    """
    Stage 3 (Rules): Fast, local rules-based extraction.
    Returns a dictionary of extracted attributes and generated descriptions.
    """
    extracted = {}
    
    brand = row.get("BRAND_NAME", row.get("E1_Brand", row.get("Part_Manuf", "")))
    if not brand or brand.startswith("--"):
        brand = row.get("Part_Manuf", "Unknown Brand")
    
    mpn = row.get("Mfg_Part_Num", "")
    desc = row.get("Part_Desc", "") + " " + row.get("Part_Manuf", "")
    
    if not desc.strip():
        return extracted

    # Dictionary to hold dynamic attributes for the ATTRIBUTE_LABEL schema
    dynamic_attrs = []
        
    # Voltage
    voltage_match = re.search(r'\b(\d{2,3})\s*(?:V|v|Volts|volts|VAC|vac)\b', desc)
    if voltage_match:
        val = voltage_match.group(1)
        extracted["Voltage"] = f"{val} V"
        dynamic_attrs.append(("Voltage Rating", val, "V"))
        
    # Amps
    amps_match = re.search(r'\b(\d{1,3}(?:\.\d+)?)\s*(?:A|a|Amps|amps)\b', desc)
    if amps_match:
        val = amps_match.group(1)
        extracted["Amperage"] = f"{val} A"
        dynamic_attrs.append(("Amperage Rating", val, "A"))
        
    # Material
    material = ""
    if re.search(r'\b(?:Stainless\s*Steel|SS)\b', desc, re.IGNORECASE):
        material = "Stainless Steel"
    elif re.search(r'\b(?:Brass)\b', desc, re.IGNORECASE):
        material = "Brass"
    elif re.search(r'\b(?:Plastic)\b', desc, re.IGNORECASE):
        material = "Plastic"
    
    if material:
        extracted["Material"] = material
        dynamic_attrs.append(("Material", material, ""))
        
    # Dimensions W x D x H (e.g. 24 in W x 24-1/4 in D)
    w_match = re.search(r'\b(\d+(?:-\d+/\d+|\.\d+)?)\s*(?:in|inch|inches|")\s*W\b', desc, re.IGNORECASE)
    if w_match:
        extracted["WIDTH"] = w_match.group(1)
        extracted["WIDTH_UOM"] = "in"
        
    d_match = re.search(r'\b(\d+(?:-\d+/\d+|\.\d+)?)\s*(?:in|inch|inches|")\s*D\b', desc, re.IGNORECASE)
    if d_match:
        extracted["LENGTH"] = d_match.group(1)
        extracted["LENGTH_UOM"] = "in"
        
    h_match = re.search(r'\b(\d+(?:-\d+/\d+|\.\d+)?)\s*(?:in|inch|inches|")\s*H\b', desc, re.IGNORECASE)
    if h_match:
        extracted["HEIGHT"] = h_match.group(1)
        extracted["HEIGHT_UOM"] = "in"

    # W x L (e.g. 1/2"x18", 1/2" x 18")
    wxl_match = re.search(r'(\d+(?:/\d+)?)(?:"|in|inch|inches)?\s*[xX]\s*(\d+(?:/\d+)?)(?:"|in|inch|inches)?', desc)
    if wxl_match:
        extracted["WIDTH"] = wxl_match.group(1)
        extracted["WIDTH_UOM"] = "in"
        extracted["LENGTH"] = wxl_match.group(2)
        extracted["LENGTH_UOM"] = "in"

    # Grit Size (e.g. P150, P120)
    grit_match = re.search(r'\bP(\d{2,4})\b', desc)
    if grit_match:
        val = grit_match.group(1)
        dynamic_attrs.append(("Grit Size", val, ""))
    
    # Pack Quantity (e.g. 6pc, 50 Disc/Box, 100/Box)
    pack_match = re.search(r'\b(\d+)\s*(?:pc|Disc/Box|/Box|pk|pack|pcs)\b', desc, re.IGNORECASE)
    if pack_match:
        extracted["Selling Qty"] = pack_match.group(1)

    # Simple category extraction
    category = ""
    categories = ["Sanding Belt", "Disc", "Dishwasher", "Widget", "Valve", "Fitting", "Faucet"]
    for cat in categories:
        if re.search(rf'\b{cat}\b', desc, re.IGNORECASE):
            category = cat
            extracted["CATEGORY"] = cat
            break

    # Map dynamic attributes to ATTRIBUTE_LABEL schema
    for i, (label, val, uom) in enumerate(dynamic_attrs, start=1):
        if i <= 50:  # Max 50 attributes supported
            extracted[f"ATTRIBUTE_LABEL {i}"] = label
            extracted[f"ATTRIBUTE_VALUE {i}"] = val
            extracted[f"ATTRIBUTE_UOM {i}"] = uom

    # Build description string from available attributes
    attr_parts = []
    if "Voltage" in extracted: attr_parts.append(extracted["Voltage"])
    if "Amperage" in extracted: attr_parts.append(extracted["Amperage"])
    if "Material" in extracted: attr_parts.append(extracted["Material"])
    for i in range(1, len(dynamic_attrs) + 1):
        if extracted.get(f"ATTRIBUTE_LABEL {i}") == "Grit Size":
            attr_parts.append(f"Grit {extracted[f'ATTRIBUTE_VALUE {i}']}")

    # Form dimensions string
    dim_parts = []
    if "WIDTH" in extracted: dim_parts.append(f"{extracted['WIDTH']} {extracted['WIDTH_UOM']} W")
    if "LENGTH" in extracted: dim_parts.append(f"{extracted['LENGTH']} {extracted['LENGTH_UOM']} D/L")
    if "HEIGHT" in extracted: dim_parts.append(f"{extracted['HEIGHT']} {extracted['HEIGHT_UOM']} H")
    
    if dim_parts:
        attr_parts.append(" x ".join(dim_parts))

    attr_str = ", ".join(attr_parts)
    
    # Fallback to Part_Desc if category is empty to still have meaningful descriptions
    base_name = category if category else "Product"

    # Generate Descriptions
    # 1. INVOICE_DESC: Max 40 chars, uppercase
    raw_invoice = f"{brand} {base_name} {attr_str}".replace(" ,", ",").strip(", ")
    extracted["INVOICE_DESC"] = raw_invoice[:40].upper()
    
    # 2. SHORT_DESC: Brand + Category + MPN + Attributes
    extracted["SHORT_DESC"] = f"{brand} {mpn} {base_name}, {attr_str}".strip(", ")
    
    # 3. LONG_DESC1: Brand + Category + Attributes
    extracted["LONG_DESC1"] = f"{brand} {base_name}, {attr_str}".strip(", ")
    
    # 4. RETAIL_DESC: Consumer-friendly
    extracted["RETAIL_DESC"] = f"{brand} {base_name} ({attr_str})".strip(" ()")

    return extracted
