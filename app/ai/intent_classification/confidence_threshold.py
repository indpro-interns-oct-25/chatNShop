from typing import List, Dict, Any, Tuple

# --- Configuration for Confidence ---

# The absolute minimum score required for any result to be considered valid.
MIN_ABSOLUTE_CONFIDENCE = 0.70

# The minimum required score difference between the top two results
# to consider the top result unambiguous. If the gap is smaller than this,
# the result is ambiguous.
MIN_DIFFERENCE_THRESHOLD = 0.10


def is_confident(results: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Evaluates a list of ranked results to determine if the outcome is confident.

    This function checks two conditions:
    1. The top result's score must be above the MIN_ABSOLUTE_CONFIDENCE.
    2. If there are multiple results, the score gap between the first and second
       must be greater than the MIN_DIFFERENCE_THRESHOLD.

    Args:
        results: A list of result dictionaries, sorted by score in descending order.
                 Each dict must contain a 'score' key.

    Returns:
        A tuple containing:
        - A boolean indicating if the result is confident (True) or not (False).
        - A string reason for the outcome (e.g., "CONFIDENT", "AMBIGUOUS", "BELOW_THRESHOLD").
    """
    # Case 1: No results were found.
    if not results:
        return False, "NO_RESULTS"

    top_result = results[0]

    # Case 2: The top result's score is below the absolute minimum required.
    if top_result['score'] < MIN_ABSOLUTE_CONFIDENCE:
        return False, "BELOW_THRESHOLD"

    # Case 3: There is only one result, and it's above the threshold.
    if len(results) == 1:
        return True, "CONFIDENT_SINGLE_RESULT"

    # Case 4: There are multiple results. Check for ambiguity.
    second_result = results[1]
    difference = top_result['score'] - second_result['score']

    if difference < MIN_DIFFERENCE_THRESHOLD:
        return False, "AMBIGUOUS"

    # If all checks pass, the result is confident.
    return True, "CONFIDENT"
