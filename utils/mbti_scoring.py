from .questionnaire import SIXTY_QUESTIONS

PAIRS = [('E', 'I'), ('S', 'N'), ('T', 'F'), ('J', 'P')]
_OPPOSITE = {**{a: b for a, b in PAIRS}, **{b: a for a, b in PAIRS}}

RESPONSE_MAP = {
    'strongly_disagree': 1, 'disagree': 2, 'neutral': 3,
    'agree': 4, 'strongly_agree': 5
}


def _rating(response):
    """Convert a response (1-5 or a label) to an int rating, clamped to 1-5."""
    if isinstance(response, str) and not response.strip().isdigit():
        return RESPONSE_MAP.get(response, 3)
    return max(1, min(5, int(response)))


def traditional_mbti_score(responses, questions=None):
    """Score responses on each MBTI dimension pair.

    Each question is keyed to one pole (e.g. 'E'). Agreeing pushes toward that
    pole and disagreeing pushes toward the opposite pole ('I'); neutral (3)
    contributes nothing. Each pair's score is normalised by the number of
    questions answered for that pair, so unequal question counts per pole do
    not bias the result and an all-neutral questionnaire scores 0.5 everywhere.

    Args:
        responses: mapping of question id -> rating (1-5 or a label).
        questions: the questions that were asked (each with 'id' and
            'dimension'). Defaults to the built-in question bank, which covers
            the 20/40/60-question sets.

    Returns:
        Dict like {'E_score': 0.6, 'I_score': 0.4, ...}; each pair sums to 1.
    """
    if questions is None:
        questions = SIXTY_QUESTIONS
    # Compare ids as strings so int/str keys (JSON round-trips) both match
    question_dimensions = {str(q['id']): q['dimension'] for q in questions}

    net = {a: 0 for a, _ in PAIRS}    # signed agreement toward the first pole
    count = {a: 0 for a, _ in PAIRS}  # questions answered per pair

    for question_id, response in responses.items():
        dimension = question_dimensions.get(str(question_id))
        if dimension not in _OPPOSITE:
            continue
        agreement = _rating(response) - 3  # -2 .. +2
        first = dimension if dimension in net else _OPPOSITE[dimension]
        net[first] += agreement if dimension == first else -agreement
        count[first] += 1

    result = {}
    for a, b in PAIRS:
        if count[a]:
            score_a = 0.5 + net[a] / (4 * count[a])  # maps to 0.0 .. 1.0
        else:
            score_a = 0.5
        result[f'{a}_score'] = score_a
        result[f'{b}_score'] = 1 - score_a

    return result


def determine_mbti_type(scores):
    """Determine MBTI type from scores.

    An exact tie (0.5/0.5) has no preference; it resolves to the second letter
    of the pair (I, N, F, P) so the result is always a valid four-letter type.
    """
    return "".join(
        a if scores.get(f'{a}_score', 0) > scores.get(f'{b}_score', 0) else b
        for a, b in PAIRS
    )


if __name__ == "__main__":
    # Test scoring
    test_responses = {
        1: 4, 2: 5, 3: 3, 4: 4, 5: 3,
        6: 2, 7: 4, 8: 4, 9: 5, 10: 3,
        11: 4, 12: 2, 13: 4, 14: 3, 15: 4,
        16: 5, 17: 4, 18: 4, 19: 3, 20: 2
    }

    scores = traditional_mbti_score(test_responses)
    mbti_type = determine_mbti_type(scores)
    print(f"Scores: {scores}")
    print(f"MBTI Type: {mbti_type}")
