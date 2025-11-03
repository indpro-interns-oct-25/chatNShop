import re
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class EntityExtractor:
    def __init__(self):
        logger.info("✅ EntityExtractor initialized.")

    def extract_entities(self, text: str):
        """Main method to extract entities from user input."""
        logger.info(f"🔍 Extracting entities from: {text}")

        text_lower = text.lower()

        # --- Brand extraction ---
        brand = None
        known_brands = ["nike", "adidas", "puma", "reebok", "apple", "samsung"]
        for b in known_brands:
            if b in text_lower:
                brand = b
                break

        # --- Color extraction ---
        color = None
        known_colors = ["red", "blue", "black", "white", "green", "yellow"]
        for c in known_colors:
            if c in text_lower:
                color = c
                break

        # --- Product name / category ---
        product_name = None
        known_products = ["shoes", "phone", "t-shirt", "watch", "laptop"]
        for p in known_products:
            if p in text_lower:
                product_name = p
                break

        # --- Size extraction ---
        size = None
        match = re.search(r"size\s*(\d+)", text_lower)
        if match:
            size = match.group(1)

        # --- Price range (under / below / between / from-to) ---
        price_range = {"min": None, "max": None, "currency": "INR"}

        # Case: under or below a price
        if "under" in text_lower or "below" in text_lower:
            match = re.search(r"(?:under|below)\s*\$?(\d+)", text_lower)
            if match:
                price_range["max"] = int(match.group(1))
                price_range["currency"] = "USD" if "$" in text_lower else "INR"

        # Case: from-to or between prices
        elif ("from" in text_lower and "to" in text_lower) or "between" in text_lower:
            match = re.search(r"(?:from|between)\s*\$?(\d+)\s*(?:to|and)\s*\$?(\d+)", text_lower)
            if match:
                price_range["min"] = int(match.group(1))
                price_range["max"] = int(match.group(2))
                price_range["currency"] = "USD" if "$" in text_lower else "INR"

        entities = {
            "product_name": product_name,
            "brand": brand,
            "color": color,
            "size": size,
            "price_range": price_range,
            "category": None
        }

        logger.info(f"🎯 Extracted Entities: {entities} (from: {text})")
        return entities
