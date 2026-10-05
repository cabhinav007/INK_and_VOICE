import re
from typing import Tuple
from app.core.constants import EMOTION_TRIGGERS

class EmotionEngine:
    @staticmethod
    def detect_emotion(quote: str, context: str) -> str:
        """Scans speech tags and dialogue content for emotional triggers."""
        text_to_scan = f"{quote} {context}".lower()
        
        for emotion, keywords in EMOTION_TRIGGERS.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', text_to_scan):
                    return emotion
        return "neutral"

    @staticmethod
    def get_emotion_params(emotion: str, age_group: str, gender: str = "Female") -> Tuple[float, float]:
        """
        Returns (target_speed_multiplier, pitch_factor) for a given
        emotion + age + gender combination.
        """
        speed = 0.98  # Relaxed base rate for realistic speech pacing
        pitch = 1.0

        # Age adjustments (subtle pitch shifts to retain organic resonance)
        if age_group in ("Child", "Young"):
            pitch = 1.08 if gender == "Female" else 1.05
            speed = 0.94  # Speak slightly slower for child-like clarity
        elif age_group == "Senior":
            pitch = 0.94 if gender == "Female" else 0.90
            speed = 0.90  # Measured, seasoned deliveryk

        # Emotion adjustments (accentuated pitch and pace modulation for dynamic expressiveness)
        if emotion == "sad":
            speed *= 0.70  # Slower, solemn delivery
            pitch *= 0.82  # Lower, melancholic pitch
        elif emotion == "joy":
            speed *= 1.20  # Energetic, bright pace
            pitch *= 1.20  # Elevated, joyful pitch
        elif emotion == "angry":
            speed *= 1.20  # Faster, tense delivery
            pitch *= 1.12  # Higher, intense pitch

        return speed, pitch

    @staticmethod
    def apply_neural_styling(text: str, emotion: str) -> str:
        """
        Dynamically manipulates the text string before passing it to the neural generator
        to cue natural human actor-like intonations (e.g. forcefulness or hesitations).
        """
        styled_text = text
        if emotion == "angry":
            if not styled_text.endswith("!") and not styled_text.endswith("?"):
                styled_text = styled_text.rstrip(".") + "!"
            elif styled_text.endswith("?"):
                styled_text = styled_text.rstrip("?") + "?!"
        elif emotion == "sad":
            # Add ellipses to create dramatic pauses and sigh-like intonations
            styled_text = "... " + styled_text.replace(", ", "... ").replace(". ", "... ") + "..."
        return styled_text
