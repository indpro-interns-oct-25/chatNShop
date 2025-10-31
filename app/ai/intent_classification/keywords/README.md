# Keyword Dictionaries

Schema
- intent: { priority: number, keywords: string[] }
- priority: 1 = highest within file
- keywords: include single- and multi-word phrases

Guidelines
- 20–30 keywords per intent (min 20 enforced)
- Include synonyms, colloquialisms, common misspellings
- Include both UK/US spellings (colour/color, favourite/favorite, jewellery/jewelry)
- At least 5 multi-word phrases per intent
- Include hyphenated/spaced variants where common (e.g., e-mail/email)

Weights
- Lower number = higher priority; keep 1–9 per file.

Maintenance
- Run linter/tests before commit to validate count, duplicates, encoding
- Monthly review; feed ambiguous logs into additions

Testing
- Unit tests assert: min count, multi-word presence, no duplicates (case-insensitive)
