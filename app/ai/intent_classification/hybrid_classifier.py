"""
Hybrid Classifier
Implements weighted scoring algorithm to combine keyword and embedding matching results.

import re

class HybridIntentClassifier:
    """
    Hybrid Intent Classifier:
    Combines simple keyword + pattern rules with entity extraction.
    Later you can plug in an LLM model or vector search if needed.
    """

    def __init__(self):
        self.intent_keywords = {
            "search": ["show", "find", "buy", "looking for", "search", "need"],
            "cancel": ["cancel", "stop", "abort"],
            "track": ["track", "status", "order"],
            "greeting": ["hi", "hello", "hey"]
        }

    def classify(self, text: str):
        text_lower = text.lower()

        # ----- Intent Detection -----
        intent = "unknown"
        confidence = 0.5
        for key, words in self.intent_keywords.items():
            if any(w in text_lower for w in words):
                intent = key.upper()
                confidence = 0.9
                break

        # ----- Entity Extraction -----
        entities = self.extract_entities(text_lower)

        # ----- Fake Search Results -----
        search_results = []
        if intent == "SEARCH" and entities.get("product_name"):
            search_results = [
                {
                    "product_name": f"{entities.get('brand', '').title()} {entities['product_name'].title()}",
                    "brand": entities.get("brand"),
                    "price": 2999,
                    "color": entities.get("color")
                }
            ]

        return {
            "action_code": intent,
            "confidence": confidence,
            "entities": entities,
            "search_results": search_results,
            "original_text": text
        }

    def extract_entities(self, text: str):
        """Extracts structured entities like brand, color, price, etc."""
        brand_list = ["nike", "puma", "adidas", "reebok", "apple", "samsung"]
        colors = ["red", "blue", "black", "white", "green", "yellow"]

        brand = next((b for b in brand_list if b in text), None)
        color = next((c for c in colors if c in text), None)
        price_match = re.search(r"(\d{3,6})", text)
        price = float(price_match.group(1)) if price_match else None

        entities = {
            "product_name": self.detect_product(text),
            "brand": brand,
            "color": color,
            "size": self.detect_size(text),
            "price_range": {"min": None, "max": price, "currency": "INR"} if price else None,
            "category": self.detect_category(text)
        }

        return entities

    def detect_product(self, text: str):
        words = ["shoe", "shoes", "tshirt", "shirt", "phone", "laptop", "watch", "bag"]
        for w in words:
            if w in text:
                return w
        return None

    def detect_category(self, text: str):
        if "electronics" in text or "phone" in text or "laptop" in text:
            return "Electronics"
        if "shoe" in text or "shirt" in text or "tshirt" in text:
            return "Fashion"
        return None

    def detect_size(self, text: str):
        size_match = re.search(r"\b(size\s*\d{1,2})\b", text)
        return size_match.group(1) if size_match else None
This module implements TASK-5: Hybrid Matching Strategy by blending results from
both keyword and embedding matchers using configurable weights.
"""
from typing import List, Dict, Any
from app.ai.config import WEIGHTS  # Fallback weights


class HybridClassifier:
    """
    Blends keyword and embedding matching results using weighted scoring.
    
    This class implements the core hybrid matching strategy (TASK-5) by:
    1. Combining results from both keyword and embedding matchers
    2. Applying configurable weights to each method's scores
    3. Resolving conflicts deterministically
    4. Returning sorted blended results
    """
    
    def __init__(self, kw_weight: float = None, emb_weight: float = None):
        """
        Initialize classifier with weights.
        
        Args:
            kw_weight: Weight for keyword scores (default from config)
            emb_weight: Weight for embedding scores (default from config)
        """
        self.kw_weight = kw_weight or WEIGHTS.get("keyword", 0.6)
        self.emb_weight = emb_weight or WEIGHTS.get("embedding", 0.4)
    
    def blend(self, kw_results: List[Dict], emb_results: List[Dict]) -> List[Dict]:
        """
        Blend keyword and embedding results using weighted scoring.
        
        Args:
            kw_results: List of keyword matching results, each with 'id', 'score', etc.
            emb_results: List of embedding matching results, each with 'id', 'score', etc.
            
        Returns:
            List of blended results sorted by blended score (descending).
            Each result includes:
            - id: Intent/action code
            - score: Blended score (weighted average)
            - source: 'blended'
            - keyword_score: Original keyword score
            - embedding_score: Original embedding score
            - All other fields from the base result
        """
        # Edge cases: return non-empty results if one is empty
        if not kw_results and not emb_results:
            return []
        
        if not kw_results:
            return emb_results
        
        if not emb_results:
            return kw_results
        
        # Create mapping of intent IDs to scores from both methods
        intent_scores: Dict[str, Dict[str, Any]] = {}
        
        # Process keyword results
        for result in kw_results:
            intent_id = result.get('id') or result.get('intent', 'unknown')
            score = result.get('score', 0.0)
            intent_scores[intent_id] = {
                'keyword_score': score,
                'keyword_result': result,
                'embedding_score': 0.0,
                'embedding_result': None
            }
        
        # Process embedding results
        for result in emb_results:
            intent_id = result.get('id') or result.get('intent', 'unknown')
            score = result.get('score', 0.0)
            
            if intent_id in intent_scores:
                # Intent exists in keyword results - merge
                intent_scores[intent_id]['embedding_score'] = score
                intent_scores[intent_id]['embedding_result'] = result
            else:
                # New intent from embedding results only
                intent_scores[intent_id] = {
                    'keyword_score': 0.0,
                    'keyword_result': None,
                    'embedding_score': score,
                    'embedding_result': result
                }
        
        # Calculate blended scores
        blended_results = []
        
        for intent_id, scores in intent_scores.items():
            # Weighted average of scores
            blended_score = (
                scores['keyword_score'] * self.kw_weight + 
                scores['embedding_score'] * self.emb_weight
            )
            
            # Conflict resolution: use result with higher individual score as base
            if scores['keyword_score'] > scores['embedding_score']:
                base_result = scores['keyword_result']
            else:
                base_result = scores['embedding_result']
            
            if base_result:
                # Create blended result preserving all original fields
                blended_result = base_result.copy()
                blended_result['score'] = blended_score
                blended_result['source'] = 'blended'
                blended_result['keyword_score'] = scores['keyword_score']
                blended_result['embedding_score'] = scores['embedding_score']
                blended_results.append(blended_result)
        
        # Sort by blended score (descending)
        blended_results.sort(key=lambda x: x.get('score', 0.0), reverse=True)
        return blended_results
    
    def update_weights(self, kw_weight: float, emb_weight: float) -> None:
        """
        Update blending weights (for hot-reload support).
        
        Args:
            kw_weight: New weight for keyword scores
            emb_weight: New weight for embedding scores
        """
        self.kw_weight = kw_weight
        self.emb_weight = emb_weight

