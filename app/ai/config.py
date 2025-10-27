"""
Configuration File for the AI Module

This file stores all the settings, weights, and thresholds needed by
the intent classification models.
"""

# --- Keyword Matcher Settings ---

# If a keyword match has a score >= this value, we'll return it
# immediately and skip the (slower) embedding search.
# Set to 1.0 to only prioritize exact "perfect" matches.
PRIORITY_THRESHOLD = 0.95


# --- Hybrid Blending Weights ---

# Defines how to combine the scores from the two different matchers.
# These should ideally add up to 1.0, but it's not strictly required.
WEIGHTS = {
    "keyword": 0.6,    # Give more weight to explicit keywords
    "embedding": 0.4   # Give less weight to semantic "guesses"
}


# --- Confidence Thresholds (for confidence_threshold.py) ---

# The absolute minimum score required for any result to be considered valid.
MIN_ABSOLUTE_CONFIDENCE = 0.70

# The minimum required score difference between the top two results
# to consider the top result unambiguous. If the gap is smaller than this,
# the result is "AMBIGUOUS".
MIN_DIFFERENCE_THRESHOLD = 0.10
