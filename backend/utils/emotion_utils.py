# emotion_utils.py

from typing import List, Dict
from difflib import get_close_matches

# Robert Plutchik's 8 basic emotions
BASIC_EMOTIONS = [
    'joy', 'trust', 'fear', 'surprise', 'sadness', 'disgust', 'anger', 'anticipation'
]

# Common replacements for non-standard emotions
EMOTION_REPLACEMENTS = {
    'happiness': 'joy',
    'contentment': 'joy',
    'love': 'joy',
    'confidence': 'trust',
    'hope': 'anticipation',
    'curiosity': 'anticipation',
    'anxiety': 'fear',
    'stress': 'fear',
    'shock': 'surprise',
    'confusion': 'surprise',
    'grief': 'sadness',
    'disappointment': 'sadness',
    'envy': 'disgust',
    'boredom': 'disgust',
    'rage': 'anger',
    'frustration': 'anger',
    'resentment': 'anger',
    'embarrassment': 'fear',
}

# Structure of blended emotions (dyads)
DYAD_DICT = {
    'love': ('joy', 'trust'),
    'submission': ('trust', 'fear'),
    'alarm': ('fear', 'surprise'),
    'disappointment': ('surprise', 'sadness'),
    'remorse': ('sadness', 'disgust'),
    'contempt': ('disgust', 'anger'),
    'aggressiveness': ('anger', 'anticipation'),
    'optimism': ('anticipation', 'joy')
}

# Emotion intensity mapping
INTENSITY_MAP = {
    'anger':       ('Annoyance', 'Anger', 'Rage'),
    'anticipation':('Interest', 'Anticipation', 'Vigilance'),
    'joy':         ('Serenity', 'Joy', 'Ecstasy'),
    'trust':       ('Acceptance', 'Trust', 'Admiration'),
    'fear':        ('Apprehension', 'Fear', 'Terror'),
    'surprise':    ('Distraction', 'Surprise', 'Amazement'),
    'sadness':     ('Pensiveness', 'Sadness', 'Grief'),
    'disgust':     ('Boredom', 'Disgust', 'Loathing')
}

def detect_blend_emotions(
    emotion_score_dict: Dict[str, float],
    threshold: float = 0.1,
    method: str = 'average'
) -> Dict[str, float]:
    """
    Detect if basic emotion combinations form blended emotions (dyads) and return blended emotions with estimated intensity.

    Parameters:
    - emotion_score_dict: e.g. {'joy': 0.6, 'trust': 0.4, 'fear': 0.2}
    - threshold: If both basic emotions' scores are greater than this value, they form a blended emotion
    - method: Calculation method for blended emotion score: 'average' or 'min'

    Returns:
    - dict: Blended emotion names and their scores
    """
    blend_emotions = {}
    for blend, (e1, e2) in DYAD_DICT.items():
        if e1 in emotion_score_dict and e2 in emotion_score_dict:
            s1, s2 = emotion_score_dict[e1], emotion_score_dict[e2]
            if s1 >= threshold and s2 >= threshold:
                if method == 'average':
                    score = round((s1 + s2) / 2, 3)
                elif method == 'min':
                    score = round(min(s1, s2), 3)
                else:
                    raise ValueError("Invalid method. Use 'average' or 'min'.")
                blend_emotions[blend] = score
    return blend_emotions

def standardize_emotions(
    emotion_list,
    replacements_dict: Dict[str, str] = EMOTION_REPLACEMENTS,
    basic_emotions: List[str] = BASIC_EMOTIONS,
    use_fuzzy_match: bool = False
) -> List[str]:
    """
    Standardize input emotion list to one of Robert Plutchik's eight basic emotions.
    Supports input as list or dictionary (only processes keys for dictionary).

    Features:
    - Supports common emotion word replacements (e.g. 'happiness' → 'joy').
    - Supports fuzzy matching (optional), normalizing similarly spelled emotion words to basic emotions.
    - Outputs deduplicated basic emotion list maintaining input order.
    - Unrecognized emotions are skipped with printed warnings.

    Parameters:
        emotion_list: List of emotion strings to be standardized.
        replacements_dict: Custom emotion replacement dictionary.
        basic_emotions: Basic emotion list (default: Plutchik's eight basic emotions).
        use_fuzzy_match: Whether to enable fuzzy matching.

    Returns:
        Standardized basic emotion list (deduplicated with order preserved).
    """
    # If input is dictionary, take its keys as emotion list
    if isinstance(emotion_list, dict):
        emotion_list = list(emotion_list.keys())

    standardized = []
    for emotion in emotion_list:
        e = emotion.lower()
        if e in basic_emotions:
            standardized.append(e)
        elif e in replacements_dict:
            standardized.append(replacements_dict[e])
        elif use_fuzzy_match:
            match = get_close_matches(e, basic_emotions, n=1, cutoff=0.7)
            if match:
                print(f"🔍 Fuzzy matched '{emotion}' → '{match[0]}'")
                standardized.append(match[0])
            else:
                print(f"⚠️ Unrecognized emotion: {emotion}, skipped")
        else:
            print(f"⚠️ Unrecognized emotion: {emotion}, skipped")

    # ✅ Deduplicate and preserve order
    seen = set()
    unique_ordered = []
    for e in standardized:
        if e not in seen:
            seen.add(e)
            unique_ordered.append(e)
    return unique_ordered

# Example usage:
if __name__ == "__main__":
    raw_emotions = ['joy', 'confidence', 'fear', 'hope', 'envy']
    result = standardize_emotions(raw_emotions, use_fuzzy_match=True)
    print("Standardization result:", result)

    example_scores = {
        'joy': 0.6,
        'trust': 0.4,
        'fear': 0.2,
        'anticipation': 0.5,
        'anger': 0.4
    }
    result = detect_blend_emotions(example_scores)
    print("Blended emotion detection result:", result)
