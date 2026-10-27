import urllib.parse
from typing import List, Dict, Any, Optional

# Pharmacy search URL templates
PHARMACY_CONFIGS = [
    {
        "id": "tata_1mg",
        "name": "Tata 1mg",
        "base_url": "https://www.1mg.com",
        "search_url_template": "https://www.1mg.com/search/all?name={query}",
        "icon": "1mg",
        "delivery_note": "Standard home delivery available in major Indian cities. Final delivery charges calculated at checkout."
    },
    {
        "id": "pharmeasy",
        "name": "PharmEasy",
        "base_url": "https://pharmeasy.in",
        "search_url_template": "https://pharmeasy.in/search/all?name={query}",
        "icon": "pharmeasy",
        "delivery_note": "Delivery time depends on pincode. Pincode and prescription required at checkout."
    },
    {
        "id": "apollo",
        "name": "Apollo Pharmacy",
        "base_url": "https://www.apollopharmacy.in",
        "search_url_template": "https://www.apollopharmacy.in/search-medicines/{query}",
        "icon": "apollo",
        "delivery_note": "Fast 2-hour or same-day delivery available in supported locations."
    },
    {
        "id": "netmeds",
        "name": "Netmeds",
        "base_url": "https://www.netmeds.com",
        "search_url_template": "https://www.netmeds.com/catalogsearch/result/{query}/all",
        "icon": "netmeds",
        "delivery_note": "Pan-India delivery with prescription upload support."
    }
]


def build_pharmacy_search_link(pharmacy_id: str, medicine_query: str) -> str:
    """
    Construct direct verified search link for an online pharmacy.
    Properly URL-encodes queries to prevent injection or invalid URLs.
    """
    encoded = urllib.parse.quote_plus(medicine_query.strip())
    for p in PHARMACY_CONFIGS:
        if p["id"] == pharmacy_id:
            return p["search_url_template"].format(query=encoded)
    # Default fallback to 1mg search
    return f"https://www.1mg.com/search/all?name={encoded}"


def get_pharmacy_listings(
    medicine_name: str,
    active_ingredient: Optional[str] = None,
    strength: Optional[str] = None,
    dosage_form: Optional[str] = None,
    pack_size: Optional[str] = None,
    is_rx_required: bool = False,
    max_providers: int = 3
) -> List[Dict[str, Any]]:
    """
    Build direct search listings for up to max_providers suitable pharmacies.
    Strictly observes pricing honesty:
      - Major Indian e-pharmacies enforce Cloudflare bot protection and dynamic session tokens.
      - Never fabricate live prices, stock levels, or discounts.
      - Provides authentic, direct search links to the specific medicine on each pharmacy.
      - Stamps status as 'unverified_link_only' with message 'Price not verified — check the pharmacy website'.
    """
    listings = []
    selected_configs = PHARMACY_CONFIGS[:max_providers]

    clean_name = medicine_name.strip()
    search_query = clean_name
    if strength and strength.lower() not in clean_name.lower():
        search_query = f"{clean_name} {strength}"

    for config in selected_configs:
        search_url = build_pharmacy_search_link(config["id"], search_query)

        listings.append({
            "pharmacy_id": config["id"],
            "pharmacy_name": config["name"],
            "matching_medicine_name": clean_name,
            "brand": clean_name.split()[0] if clean_name else "",
            "active_ingredient": active_ingredient or "Check packaging / verified catalog",
            "strength": strength or "Standard dosage",
            "dosage_form": dosage_form or "Tablet / Capsule",
            "pack_size": pack_size or "Standard strip",
            "is_rx_required": is_rx_required,
            # Strict compliance: honest link-only mode
            "price_status": "unverified_link_only",
            "verified_price": None,
            "discounted_price": None,
            "price_display": "Price not verified — check pharmacy website",
            "availability": "Check live stock on pharmacy site",
            "delivery_note": config["delivery_note"],
            "direct_url": search_url,
            "action_label": f"View at {config['name']}"
        })

    return listings
