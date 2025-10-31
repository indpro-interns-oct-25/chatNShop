"""
Decision Engine
This file contains the main logic for the intent classification.
Now integrated with config manager for dynamic configuration and A/B testing.
"""
import logging
import time
from typing import Any, Dict, List, Optional

# --- CONFIG MANAGER INTEGRATION ---
# Import config manager for dynamic configuration
from app.core.config_manager import CONFIG_CACHE, ACTIVE_VARIANT
from app.ai.config import PRIORITY_THRESHOLD, WEIGHTS  # Fallback config
from app.ai.intent_classification.contracts import RuleDecision
from app.ai.intent_classification.keyword_matcher import KeywordMatcher
from app.ai.intent_classification.embedding_matcher import EmbeddingMatcher
from app.ai.intent_classification.hybrid_classifier import HybridClassifier
from app.ai.intent_classification import confidence_threshold
# Optional LLM fallback
try:
    from app.ai.llm_intent.request_handler import RequestHandler as _LLMHandler
    from app.schemas.llm_intent import LLMIntentRequest as _LLMReq
except Exception:
    _LLMHandler = None  # type: ignore
    _LLMReq = None  # type: ignore
# --- END CONFIG MANAGER INTEGRATION ---

class DecisionEngine:
    """
    Orchestrates the hybrid search process.
    Now supports dynamic configuration via config manager.
    """
    def __init__(self):

        """
        Initializes the Decision Engine and its constituent matchers.
        Now uses config manager for dynamic configuration.
        """
        print("Initializing DecisionEngine...")
        self.keyword_matcher = KeywordMatcher()
        # Lazy-load embedding matcher to avoid loading model when disabled or in tests
        self.embedding_matcher = None
        # Initialize hybrid classifier (weights will be updated from config)
        self.hybrid_classifier = HybridClassifier()
        
        # Load settings from config manager (with fallback to static config)
        self._load_config_from_manager()
        print(f"✅ DecisionEngine Initialized: Settings loaded from config manager (variant: {ACTIVE_VARIANT})")
    
    def _load_config_from_manager(self):
        """
        Load configuration from config manager with fallback to static config.
        """
        try:
            # Import here to get fresh values
            from app.core.config_manager import CONFIG_CACHE, ACTIVE_VARIANT
            
            # Try to get rules from config manager (supports nested schema: {"rules": {"rule_sets": {...}}})
            rules_root = CONFIG_CACHE.get('rules', {})
            rules = rules_root.get('rules', rules_root)
            rule_sets = rules.get('rule_sets', {})
            current_rules = rule_sets.get(ACTIVE_VARIANT, {})
            
            # Use config manager settings if available
            if current_rules:
                self.use_embedding = current_rules.get('use_embedding', True)
                self.use_keywords = current_rules.get('use_keywords', True)
                # Load dynamic weights/thresholds if present
                self.kw_weight = current_rules.get('kw_weight', WEIGHTS.get('keyword', 0.6))
                self.emb_weight = current_rules.get('emb_weight', WEIGHTS.get('embedding', 0.4))
                self.priority_threshold = current_rules.get('priority_threshold', PRIORITY_THRESHOLD)
                # Update classifier weights
                self.hybrid_classifier.update_weights(self.kw_weight, self.emb_weight)
                print(
                    f"📋 Using config manager rules for variant {ACTIVE_VARIANT}: "
                    f"embedding={self.use_embedding}, keywords={self.use_keywords}, "
                    f"kw_weight={self.kw_weight}, emb_weight={self.emb_weight}, "
                    f"threshold={self.priority_threshold}"
                )
            else:
                # Fallback to static config (Variant A defaults)
                self.use_embedding = True
                self.use_keywords = True
                self.priority_threshold = 0.85
                self.kw_weight = 0.6
                self.emb_weight = 0.4
                # Update classifier weights
                self.hybrid_classifier.update_weights(self.kw_weight, self.emb_weight)
                print("📋 Using fallback static config (Variant A: kw=0.6, emb=0.4, threshold=0.85)")
                
        except Exception as e:
            # Fallback to static config on any error (Variant A)
            print(f"⚠️ Config manager error, using fallback: {e}")
            self.use_embedding = True
            self.use_keywords = True
            self.priority_threshold = 0.85
            self.kw_weight = 0.6
            self.emb_weight = 0.4
            # Update classifier weights
            self.hybrid_classifier.update_weights(self.kw_weight, self.emb_weight)

    def search(self, query: str) -> Dict[str, Any]:

        """
        Executes the full hybrid search flow and evaluates confidence.
        Now respects config manager settings for A/B testing.
        """
        pipeline_start = time.perf_counter()
        # Reload config in case it changed (for hot-reload)
        self._load_config_from_manager()

        keyword_results = []
        embedding_results = []
        
        rule_start = time.perf_counter()
        # Use keyword matching if enabled
        if self.use_keywords:
            keyword_results = self.keyword_matcher.search(query)
            
            # Apply the priority rule (if keywords enabled)
            if keyword_results and keyword_results[0]['score'] >= getattr(self, 'priority_threshold', PRIORITY_THRESHOLD):
                print(f"✅ Priority rule triggered. Returning high-confidence keyword match: {keyword_results[0]['id']}")
                decision = self._build_decision(
                    status="CONFIDENT_KEYWORD",
                    intent=keyword_results[0],
                    candidates=keyword_results,
                    top_confidence=keyword_results[0]['score'],
                    next_best_confidence=keyword_results[1]['score'] if len(keyword_results) > 1 else 0.0,
                    resolved_intent=keyword_results[0].get('intent'),
                    resolved_action=keyword_results[0].get('id'),
                    rule_latency_ms=self._stage_latency(rule_start),
                )
                decision.rule_latency_ms = self._stage_latency(rule_start)
                decision.handoff_metadata = {"triggered": False, "reason": None}
                payload = decision.to_payload()
                payload.update({
                    "llm_triggered": False,
                    "pipeline_latency_ms": self._stage_latency(pipeline_start),
                })
                log_latency("intent_pipeline_latency_ms", start_time=pipeline_start, tags={"llm_triggered": False, "classification_status": payload.get("classification_status")})
                return payload

        # Use embedding matching if enabled
        if self.use_embedding:
            if self.embedding_matcher is None:
                self.embedding_matcher = EmbeddingMatcher()
            embedding_results = self.embedding_matcher.search(query)
        
        # Blend results if both methods are enabled
        if self.use_keywords and self.use_embedding:
            blended_results = self.hybrid_classifier.blend(keyword_results, embedding_results)
        elif self.use_keywords and keyword_results:
            blended_results = keyword_results
        elif self.use_embedding and embedding_results:
            blended_results = embedding_results
        else:
            blended_results = []

        if not blended_results:

            # Enhanced fallback: try with lower thresholds
            print(f"⚠ No match found for query: '{query}', trying fallback...")
            
            # Fallback 1: Lower embedding threshold
            if embedding_results:
                embedding_results_lower = [r for r in embedding_results if r['score'] >= 0.3]
                if embedding_results_lower:
                    print(f"✅ Fallback found embedding match with lower threshold")
                    return self._finalize_output(
                        status="FALLBACK_EMBEDDING",
                        intent=embedding_results_lower[0],
                        config_variant=ACTIVE_VARIANT,
                        candidates=embedding_results_lower,
                        top_confidence=embedding_results_lower[0]['score'],
                        next_best_confidence=embedding_results_lower[1]['score'] if len(embedding_results_lower) > 1 else 0.0,
                        rule_latency_ms=self._stage_latency(rule_start),
                        pipeline_start=pipeline_start,
                    )
            
            # Fallback 2: Lower keyword threshold
            if keyword_results:
                keyword_results_lower = [r for r in keyword_results if r['score'] >= 0.3]
                if keyword_results_lower:
                    print(f"✅ Fallback found keyword match with lower threshold")
                    return self._finalize_output(
                        status="FALLBACK_KEYWORD",
                        intent=keyword_results_lower[0],
                        config_variant=ACTIVE_VARIANT,
                        candidates=keyword_results_lower,
                        top_confidence=keyword_results_lower[0]['score'],
                        next_best_confidence=keyword_results_lower[1]['score'] if len(keyword_results_lower) > 1 else 0.0,
                        rule_latency_ms=self._stage_latency(rule_start),
                        pipeline_start=pipeline_start,
                    )
            
            # Fallback 3: Generic search intent
            print(f"⚠ No specific match found, returning generic search intent")
            return self._finalize_output(
                status="FALLBACK_GENERIC",
                intent={
                    "id": "SEARCH_PRODUCT",
                    "intent": "SEARCH_PRODUCT",
                    "score": 0.1,
                    "source": "fallback",
                    "reason": "generic_search_fallback"
                },
                config_variant=ACTIVE_VARIANT,
                candidates=[],
                top_confidence=0.1,
                next_best_confidence=0.0,
                rule_latency_ms=self._stage_latency(rule_start),
                pipeline_start=pipeline_start,
            )

        # Evaluate final confidence
        is_confident, reason = confidence_threshold.is_confident(blended_results)

        if is_confident:

            print(f"✅ Blended result is confident. Reason: {reason}")
            decision = self._build_decision(
                status=reason,
                intent=blended_results[0],
                candidates=blended_results,
                top_confidence=blended_results[0]['score'],
                next_best_confidence=blended_results[1]['score'] if len(blended_results) > 1 else 0.0,
                resolved_intent=blended_results[0].get('intent'),
                resolved_action=blended_results[0].get('id'),
                rule_latency_ms=self._stage_latency(rule_start),
            )
            payload = self._maybe_trigger_llm(decision, query, pipeline_start)
            return payload
        else:
            # Deterministic selection on low-confidence: pick top blended action
            print(f"⚠ Blended result is NOT confident. Reason: {reason}")
            # Attempt LLM fallback if available
            if _LLMHandler and _LLMReq:
                try:
                    handler = _LLMHandler()
                    # Build minimal LLM request using top keyword/embedding confidences if present
                    top_kw = keyword_results[0]['score'] if keyword_results else 0.0
                    next_kw = keyword_results[1]['score'] if len(keyword_results) > 1 else 0.0
                    llm_req = _LLMReq(
                        user_input=query,
                        rule_intent=blended_results[0]['id'] if blended_results else None,
                        action_code=blended_results[0]['id'] if blended_results else None,
                        top_confidence=float(top_kw),
                        next_best_confidence=float(next_kw),
                        is_fallback=True,
                    )
                    llm_out = handler.handle(llm_req)
                    if llm_out and isinstance(llm_out, dict):
                        # Return LLM-resolved action_code as final
                        resolved = {
                            "id": llm_out.get("action_code"),
                            "intent": llm_out.get("action_code"),
                            "score": llm_out.get("confidence", 0.0),
                            "source": "llm",
                            "reason": "llm_fallback"
                        }
                        return {
                            "status": "LLM_FALLBACK",
                            "intent": resolved,
                            "config_variant": ACTIVE_VARIANT
                        }
                except Exception as _:
                    pass
            if blended_results:
                # If multiple with close scores, prefer one with higher embedding_score
                blended_results.sort(key=lambda x: (x.get('score', 0.0), x.get('embedding_score', 0.0)), reverse=True)
                top = blended_results[0]
                print("✅ Selecting top blended action deterministically")
                return {
                    "status": f"BLENDED_TOP_{reason}",
                    "intent": top,
                    "config_variant": ACTIVE_VARIANT
                }
            # Final fallback to generic search
            print(f"⚠ No suitable results, returning generic search")
            return self._finalize_output(
                status="FALLBACK_GENERIC",
                intent={
                    "id": "SEARCH_PRODUCT",
                    "intent": "SEARCH_PRODUCT",
                    "score": 0.1,
                    "source": "fallback",
                    "reason": "generic_search_fallback"
                },
                config_variant=ACTIVE_VARIANT,
                candidates=blended_results,
                top_confidence=blended_results[0]['score'] if blended_results else 0.1,
                next_best_confidence=blended_results[1]['score'] if len(blended_results) > 1 else 0.0,
                rule_latency_ms=self._stage_latency(rule_start),
                pipeline_start=pipeline_start,
            )



    def _build_decision(
        self,
        *,
        status: str,
        intent: Optional[Dict[str, Any]],
        candidates: List[Dict[str, Any]],
        top_confidence: float,
        next_best_confidence: float,
        resolved_intent: Optional[str],
        resolved_action: Optional[str],
        rule_latency_ms: float,
        is_fallback: bool = False,
    ) -> RuleDecision:
        confidence_gap = max(0.0, round(top_confidence - next_best_confidence, 4))
        intent_copy = dict(intent) if intent else None
        if intent_copy is not None:
            if "source" in intent_copy and "matcher_source" not in intent_copy:
                intent_copy["matcher_source"] = intent_copy["source"]
            intent_copy["source"] = "rule_based"

        candidates_copy: List[Dict[str, Any]] = []
        for candidate in candidates:
            candidate_copy = dict(candidate)
            if "source" in candidate_copy and "matcher_source" not in candidate_copy:
                candidate_copy["matcher_source"] = candidate_copy["source"]
            candidate_copy["source"] = "rule_based"
            candidates_copy.append(candidate_copy)

        decision = RuleDecision(
            classification_status=status,
            intent=intent_copy,
            candidates=candidates_copy,
            top_confidence=top_confidence,
            next_best_confidence=next_best_confidence,
            confidence_gap=confidence_gap,
            resolved_intent=resolved_intent,
            resolved_action_code=resolved_action,
            is_fallback=is_fallback,
            config_variant=ACTIVE_VARIANT,
            rule_latency_ms=rule_latency_ms,
        )
        return decision

    def _maybe_trigger_llm(
        self,
        decision: RuleDecision,
        query: str,
        pipeline_start: float,
    ) -> Dict[str, Any]:
        trigger_ctx = TriggerContext(
            top_confidence=decision.top_confidence,
            next_best_confidence=decision.next_best_confidence,
            action_code=decision.resolved_action_code,
            is_fallback=decision.is_fallback,
        )
        should_trigger, reason = should_trigger_llm(trigger_ctx)
        decision.needs_llm_review = should_trigger
        decision.trigger_reason = reason

        payload = decision.to_payload()
        payload.setdefault("llm_triggered", False)

        if not should_trigger:
            payload["pipeline_latency_ms"] = self._stage_latency(pipeline_start)
            log_latency(
                "intent_pipeline_latency_ms",
                start_time=pipeline_start,
                tags={"llm_triggered": False, "classification_status": payload.get("classification_status")},
            )
            return payload

        self._logger.info(
            "Escalating rule-based decision to LLM",
            extra={
                "trigger_reason": reason,
                "status": decision.classification_status,
                "top_confidence": decision.top_confidence,
                "next_best_confidence": decision.next_best_confidence,
            },
        )

        llm_request = LLMIntentRequest(
            user_input=query,
            rule_intent=decision.resolved_intent,
            action_code=decision.resolved_action_code,
            top_confidence=decision.top_confidence,
            next_best_confidence=decision.next_best_confidence,
            is_fallback=decision.is_fallback,
            metadata={
                "classification_status": decision.classification_status,
                "trigger_reason": decision.trigger_reason,
                "confidence_gap": decision.confidence_gap,
            },
        )

        try:
            llm_response = self._llm_manager.invoke(
                llm_request,
                metric_tags={
                    "trigger_reason": reason,
                    "config_variant": decision.config_variant,
                },
            )
        except (CircuitBreakerOpenError, RetryExceededError, TimeoutError) as exc:
            self._logger.warning(
                "LLM handoff failed",
                extra={
                    "reason": str(exc),
                    "trigger_reason": reason,
                    "status": decision.classification_status,
                },
            )
            payload.setdefault("handoff_metadata", {})
            payload["handoff_metadata"].update({"triggered": False, "failure": type(exc).__name__})
            payload.setdefault("llm_errors", []).append(str(exc))
        except Exception as exc:  # pragma: no cover - defensive
            self._logger.exception("Unexpected LLM handoff error", exc_info=exc)
            payload.setdefault("handoff_metadata", {})
            payload["handoff_metadata"].update({"triggered": False, "failure": "unknown"})
            payload.setdefault("llm_errors", []).append(str(exc))
        else:
            payload = self._merge_llm_payload(payload, llm_response)
            payload["llm_triggered"] = True
            payload.setdefault("handoff_metadata", {})
            payload["handoff_metadata"].update({"triggered": True, "reason": reason})
            self._logger.info(
                "LLM handoff completed",
                extra={
                    "trigger_reason": reason,
                    "llm_confidence": llm_response.get("confidence"),
                    "action_code": llm_response.get("action_code"),
                },
            )

        payload["pipeline_latency_ms"] = self._stage_latency(pipeline_start)
        log_latency(
            "intent_pipeline_latency_ms",
            start_time=pipeline_start,
            tags={
                "llm_triggered": payload.get("llm_triggered", False),
                "classification_status": payload.get("classification_status"),
            },
        )
        return payload

    def _merge_llm_payload(self, base_payload: Dict[str, Any], llm_payload: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(base_payload)
        intent_name = llm_payload.get("intent", "unknown_intent")
        action_code = llm_payload.get("action_code") or intent_name
        confidence = float(llm_payload.get("confidence", 0.0))

        intent_block = {
            "id": action_code,
            "intent": intent_name,
            "action": action_code,
            "score": round(confidence, 4),
            "source": llm_payload.get("metadata", {}).get("source", "llm"),
        }

        merged.update(
            {
                "intent": intent_block,
                "candidates": [intent_block],
                "top_confidence": round(confidence, 4),
                "classification_status": "LLM_TRIGGERED",
                "trigger_reason": llm_payload.get("metadata", {}).get("trigger_reason", merged.get("trigger_reason")),
                "resolved_intent": intent_name,
                "resolved_action_code": action_code,
                "llm_payload": llm_payload,
            }
        )
        return merged

    def _finalize_output(
        self,
        *,
        status: str,
        intent: Dict[str, Any],
        config_variant: str,
        candidates: List[Dict[str, Any]],
        top_confidence: float,
        next_best_confidence: float,
        rule_latency_ms: float,
        pipeline_start: float,
    ) -> Dict[str, Any]:
        decision = self._build_decision(
            status=status,
            intent=intent,
            candidates=candidates,
            top_confidence=top_confidence,
            next_best_confidence=next_best_confidence,
            resolved_intent=intent.get("intent"),
            resolved_action=intent.get("id"),
            rule_latency_ms=rule_latency_ms,
            is_fallback=True,
        )
        decision.needs_llm_review = True
        decision.trigger_reason = "rule_based_fallback"
        payload = decision.to_payload()
        payload.setdefault("handoff_metadata", {"triggered": False, "reason": "rule_based_fallback"})
        payload["pipeline_latency_ms"] = self._stage_latency(pipeline_start)
        payload["llm_triggered"] = False
        log_latency(
            "intent_pipeline_latency_ms",
            start_time=pipeline_start,
            tags={"llm_triggered": False, "classification_status": payload.get("classification_status")},
        )
        return payload

    @staticmethod
    def _stage_latency(start_time: float) -> float:
        return round((time.perf_counter() - start_time) * 1000, 2)


# Global instance for the main API
_decision_engine = None

def get_intent_classification(query: str) -> Dict[str, Any]:
    """
    Main function for intent classification.
    Creates a DecisionEngine instance if needed and processes the query.
    """
    global _decision_engine
    
    if _decision_engine is None:
        _decision_engine = DecisionEngine()
    
    return _decision_engine.search(query)