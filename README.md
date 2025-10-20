app/
├── ai/
│   ├── intent_classification/           # Rule-based module
│   │   ├── __init__.py
│   │   ├── intents.py                   # [Item 1]
│   │   ├── keyword_matcher.py           # [Item 3]
│   │   ├── embedding_matcher.py         # [Item 4]
│   │   ├── hybrid_classifier.py         # [Item 13]
│   │   ├── ambiguity_resolver.py        # [Item 5]
│   │   ├── confidence_threshold.py      # [Item 5]
│   │   ├── scoring.py                   # [Item 3]
│   │   ├── similarity.py                # [Item 4]
│   │   ├── decision_engine.py           # [Item 13]
│   │   └── keywords/
│   │       ├── loader.py                # [Item 2]
│   │       ├── search_keywords.json     # [Item 2]
│   │       ├── cart_keywords.json       # [Item 2]
│   │       └── product_keywords.json    # [Item 2]
│   │
│   └── llm_intent/                      # LLM module
│       ├── __init__.py
│       ├── prompts.py                   # [Item 11]
│       ├── prompt_builder.py            # [Item 11]
│       ├── openai_client.py             # [Item 12]
│       ├── request_handler.py           # [Item 12]
│       ├── response_parser.py           # [Item 12]
│       ├── context_builder.py           # [Item 17]
│       ├── context_summarizer.py        # [Item 17]
│       ├── confidence_calibrator.py     # [Item 18]
│       ├── accuracy_tracker.py          # [Item 18]
│       ├── semantic_cache.py            # [Item 19]
│       ├── cache_manager.py             # [Item 19]
│       ├── entity_extractor.py          # [Item 20]
│       ├── entity_validator.py          # [Item 20]
│       ├── error_handler.py             # [Item 21]
│       ├── fallback_manager.py          # [Item 21]
│       ├── feedback_collector.py        # [Item 24]
│       └── misclassification_analyzer.py # [Item 24]
│
├── api/v1/
│   ├── intent.py                        # [Item 6, 15]
│   ├── feedback.py                      # [Item 24]
│   ├── experiments.py                   # [Item 23]
│   └── analytics.py                     # [Item 22]
│
├── services/
│   ├── intent_service.py                # [Item 6, 15]
│   └── status_service.py                # [Item 16]
│
├── queue/
│   ├── __init__.py
│   ├── queue_manager.py                 # [Item 14]
│   ├── producer.py                      # [Item 15]
│   ├── consumer.py                      # [Item 14]
│   └── config.py                        # [Item 14]
│
├── repositories/
│   ├── intent_status_repository.py      # [Item 16]
│   ├── conversation_repository.py       # [Item 17]
│   └── classification_history_repository.py # [Item 18]
│
├── models/
│   ├── conversation.py                  # [Item 17]
│   ├── classification_history.py        # [Item 18]
│   ├── classification_feedback.py       # [Item 24]
│   └── experiment.py                    # [Item 23]
│
├── schemas/
│   ├── intent.py                        # [Item 1, 6]
│   ├── llm_intent.py                    # [Item 10]
│   ├── entities.py                      # [Item 20]
│   └── queue_messages.py                # [Item 15]
│
├── monitoring/
│   ├── __init__.py
│   ├── cost_tracker.py                  # [Item 22]
│   ├── token_counter.py                 # [Item 22]
│   ├── cost_alerting.py                 # [Item 22]
│   ├── metrics.py                       # [Item 25]
│   ├── tracing.py                       # [Item 25]
│   ├── alerting.py                      # [Item 25]
│   └── dashboards/
│       └── intent_classification.json   # [Item 25]
│
├── experiments/
│   ├── __init__.py
│   ├── ab_test_manager.py               # [Item 23]
│   ├── traffic_splitter.py              # [Item 23]
│   └── variant_config.py                # [Item 23]
│
├── core/
│   ├── config_manager.py                # [Item 8]
│   ├── version_control.py               # [Item 8]
│   └── circuit_breaker.py               # [Item 12]
│
├── utils/
│   ├── text_processing.py               # [Item 3]
│   ├── retry_logic.py                   # [Item 12, 21]
│   ├── cache_metrics.py                 # [Item 19]
│   └── entity_normalizer.py             # [Item 20]
│
├── tasks/
│   ├── cost_reporting.py                # [Item 22]
│   └── weekly_review.py                 # [Item 24]
│
└── db/
    └── redis_client.py                  # [Item 16, 19]

config/
├── keywords/                            # [Item 8]
├── prompts/                             # [Item 11]
│   ├── system_prompt.txt
│   └── few_shot_examples.json
├── thresholds.yaml                      # [Item 8]
├── classification_rules.yaml            # [Item 13]
└── models.yaml                          # [Item 4]

docs/
├── intent_taxonomy.md                   # [Item 1]
├── llm_intent_requirements.md           # [Item 10]
├── queue_architecture.md                # [Item 14]
└── intent_classification/               # [Item 9]
    ├── architecture.md
    ├── api_reference.md
    ├── keyword_maintenance.md
    ├── troubleshooting.md
    ├── performance_tuning.md
    └── examples.md

tests/
└── test_ai/
    ├── test_intent_classification/      # [Item 7]
    │   ├── test_keyword_matcher.py
    │   ├── test_embedding_matcher.py
    │   ├── test_hybrid_classifier.py
    │   └── test_api.py
    └── test_llm_intent/
        └── test_prompts.py              # [Item 11]
