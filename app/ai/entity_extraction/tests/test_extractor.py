from app.ai.entity_extraction.extractor import EntityExtractor

extractor = EntityExtractor()

def test_basic_extract():
    q = "Show me running shoes under $100 from Nike in black size 9"
    out = extractor.extract_entities(q)
    assert out["product_name"] == "shoes"
    assert out["brand"] == "nike"
    assert out["color"] == "black"
    assert out["size"] == "9"
    assert out["price_range"]["max"] == 100
    assert out["price_range"]["currency"] == "USD"

def test_price_range_between():
    q = "Phones from $200 to $500"
    out = extractor.extract_entities(q)
    assert out["product_name"] in ["phone", "phones"]
    assert out["price_range"]["min"] == 200
    assert out["price_range"]["max"] == 500
    assert out["price_range"]["currency"] == "USD"
