import re
import os
import pypdf
import docx
from typing import List, Dict, Tuple, Set

from app.core.constants import (
    SPEECH_VERBS,
    FEMALE_NAMES,
    MALE_NAMES,
    FEMALE_SUFFIXES,
    MALE_SUFFIXES,
    NON_NAME_WORDS,
)

from app.services.emotion_engine import EmotionEngine



class NovelParser:
    @staticmethod
    def extract_text(file_path: str) -> str:
        """Extracts plain text from PDF, DOCX or TXT files."""
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == ".pdf":
            text = []
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            return "\n\n".join(text)
            
        elif ext == ".docx":
            doc = docx.Document(file_path)
            return "\n\n".join([p.text for p in doc.paragraphs if p.text])
            
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    def _is_valid_name(word: str) -> bool:
        """
        Returns True only if *word* looks like a genuine proper name.
        Filters out common English words that happen to be capitalized.
        """
        if not word or len(word) < 2:
            return False
        # Must start with uppercase, rest lowercase
        if not word[0].isupper() or not word[1:].islower():
            return False
        # Must NOT be in our comprehensive non-name list
        if word in NON_NAME_WORDS:
            return False
        # Must be at least 3 characters (avoids "Do", "Go", "Be", etc.)
        if len(word) < 3:
            return False
        return True

    @staticmethod
    def _parse_paragraph_segments(paragraph: str) -> List[Tuple[str, str]]:
        """
        Statefully splits a paragraph into (type, text) segments, where type is
        either 'dialogue' or 'narrative'. Correctly handles double quotes and
        single quotes matching pairs, while ignoring contractions/apostrophes.
        """
        segments = []
        current_text = []
        in_dialogue = False
        i = 0
        n = len(paragraph)
        
        while i < n:
            char = paragraph[i]
            if char == '"':
                if in_dialogue:
                    # End of dialogue quote
                    if current_text:
                        segments.append(("dialogue", "".join(current_text).strip()))
                        current_text = []
                    in_dialogue = False
                else:
                    # Start of dialogue quote
                    if current_text:
                        segments.append(("narrative", "".join(current_text).strip()))
                        current_text = []
                    in_dialogue = True
            elif char == "'" and not in_dialogue:
                # Is it an opening single quote?
                is_opening = (i == 0 or paragraph[i-1].isspace() or paragraph[i-1] in '.,!?;:([«') and (i + 1 < n and not paragraph[i+1].isspace())
                if is_opening:
                    if current_text:
                        segments.append(("narrative", "".join(current_text).strip()))
                        current_text = []
                    in_dialogue = True
                else:
                    current_text.append(char)
            elif char == "'" and in_dialogue:
                # Is it a closing single quote or an apostrophe?
                is_closing = (i + 1 == n or paragraph[i+1].isspace() or paragraph[i+1] in '.,!?;:)]"') and (i > 0 and not paragraph[i-1].isspace())
                is_apostrophe = (i > 0 and paragraph[i-1].isalnum()) and (i + 1 < n and paragraph[i+1].isalnum())
                
                if is_closing and not is_apostrophe:
                    if current_text:
                        segments.append(("dialogue", "".join(current_text).strip()))
                        current_text = []
                    in_dialogue = False
                else:
                    current_text.append(char)
            else:
                current_text.append(char)
            i += 1
            
        if current_text:
            t = "".join(current_text).strip()
            if t:
                segments.append(("dialogue" if in_dialogue else "narrative", t))
                
        return segments

    @staticmethod
    def parse_novel(text: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Parses novel text into sequential chunks (narrative vs dialogue)
        and extracts list of identified characters with suggested demographics.
        """
        # Standardize curly quotes internally for easier parsing
        normalized_text = text.replace('\u201c', '"').replace('\u201d', '"')
        normalized_text = normalized_text.replace('\u2018', "'").replace('\u2019', "'")
        
        # Split text into paragraphs
        paragraphs = [p.strip() for p in normalized_text.split("\n\n") if p.strip()]
        # Also split on single newlines if paragraphs are too few
        if len(paragraphs) < 3:
            paragraphs = [p.strip() for p in normalized_text.split("\n") if p.strip()]
        
        chunks = []
        character_counts = {}
        last_speaker = "Narrator"
        
        # Track the two most recent active speaking characters (excluding Narrator)
        active_speakers = []
        
        for p_idx, paragraph in enumerate(paragraphs):
            segments = NovelParser._parse_paragraph_segments(paragraph)
            if not segments:
                continue
                
            # For each segment, attribute speaker individually
            for q_idx, (seg_type, seg_text) in enumerate(segments):
                if seg_type == "narrative":
                    # Narrative paragraph segment
                    text_clean = re.sub(r'^[\s,.:;\u2014-]+|[\s,.:;\u2014-]+$', '', seg_text)
                    if len(text_clean) > 3:
                        chunks.append({
                            "id": f"p_{p_idx}_n_{q_idx}",
                            "type": "narrative",
                            "text": text_clean,
                            "speaker": "Narrator",
                            "emotion": "neutral"
                        })
                else:
                    # Dialogue segment
                    if len(seg_text) < 2:
                        continue
                        
                    # Find context for this dialogue segment:
                    # 1. Look at the narrative tag immediately following it first (e.g. "dialogue" Dev asked.)
                    context = ""
                    if q_idx + 1 < len(segments) and segments[q_idx + 1][0] == "narrative":
                        context = segments[q_idx + 1][1]
                    
                    speaker = "Unknown"
                    if context:
                        speaker = NovelParser._attribute_speaker(context, last_speaker)
                        
                    # 2. Look at the narrative tag immediately preceding it (e.g. Dev said, "dialogue")
                    if speaker == "Unknown" and q_idx > 0 and segments[q_idx - 1][0] == "narrative":
                        context = segments[q_idx - 1][1]
                        speaker = NovelParser._attribute_speaker(context, last_speaker)
                        
                    # 3. Fallback: Check all narrative text in this paragraph
                    if speaker == "Unknown":
                        all_narrative = " ".join([seg[1] for seg in segments if seg[0] == "narrative"]).strip()
                        if all_narrative:
                            speaker = NovelParser._attribute_speaker(all_narrative, last_speaker)
                            
                    # 4. Alternating Turn & Vocative Address rules
                    if speaker == "Unknown" and len(active_speakers) >= 1:
                        # Vocative Address Rule: check if the dialogue addresses one of the active speakers
                        addressed_speaker = None
                        dialogue_lower = seg_text.lower()
                        for active_name in active_speakers:
                            if re.search(r'\b' + re.escape(active_name.lower()) + r'\b', dialogue_lower):
                                addressed_speaker = active_name
                                break
                        
                        if addressed_speaker:
                            # Dialogue addresses an active speaker, so speaker must be the OTHER active speaker
                            if len(active_speakers) >= 2:
                                speaker = [s for s in active_speakers if s != addressed_speaker][0]
                            else:
                                speaker = "Unknown"
                                
                        # Alternating Turn Rule: if still unknown, alternate speakers
                        if speaker == "Unknown":
                            if len(active_speakers) >= 2:
                                if last_speaker == active_speakers[0]:
                                    speaker = active_speakers[1]
                                else:
                                    speaker = active_speakers[0]
                            else:
                                speaker = active_speakers[0]
                                
                    # 5. Final fallback
                    if speaker == "Unknown":
                        speaker = last_speaker
                    if speaker == "Unknown":
                        speaker = "Narrator"
                        
                    emotion = EmotionEngine.detect_emotion(seg_text, context)
                    
                    # Track character speak count & update active speakers
                    if speaker != "Narrator" and speaker != "Unknown":
                        character_counts[speaker] = character_counts.get(speaker, 0) + 1
                        last_speaker = speaker
                        if speaker in active_speakers:
                            active_speakers.remove(speaker)
                        active_speakers.insert(0, speaker)
                        if len(active_speakers) > 2:
                            active_speakers = active_speakers[:2]
                        
                    chunks.append({
                        "id": f"p_{p_idx}_d_{q_idx}",
                        "type": "dialogue",
                        "text": seg_text,
                        "speaker": speaker,
                        "emotion": emotion
                    })
        
        # Consolidate and format character list
        characters = []
        
        # Always include the Narrator
        characters.append({
            "name": "Narrator",
            "gender": "Female",
            "ageGroup": "Mid-Age",
            "voice": "af_nicole",
            "mentions": 9999
        })
        
        # Filter: only keep characters with at least 1 speech and valid names
        sorted_chars = sorted(character_counts.items(), key=lambda x: x[1], reverse=True)
        for char_name, count in sorted_chars:
            if char_name == "Narrator":
                continue
            if not NovelParser._is_valid_name(char_name):
                continue
                
            gender, age_group = NovelParser._estimate_demographics(char_name, normalized_text)
            # Pick default Kokoro voice
            if gender == "Female":
                # Cycle through female voices
                f_voices = ["af_nicole", "af_sarah", "af_bella", "af_sky", "bf_emma", "bf_isabella", "af_heart"]
                default_voice = f_voices[len(characters) % len(f_voices)]
            else:
                m_voices = ["am_adam", "am_michael", "bm_george", "bm_lewis", "am_fenrir", "bm_daniel", "bm_fable"]
                default_voice = m_voices[len(characters) % len(m_voices)]
                
            characters.append({
                "name": char_name,
                "gender": gender,
                "ageGroup": age_group,
                "voice": default_voice,
                "mentions": count
            })
            
        return chunks, characters


    @staticmethod
    def _attribute_speaker(context: str, last_speaker: str) -> str:
        """Searches context for proper names near speech verbs to attribute speaker."""
        # Clean and split into words, keeping capitalization for name check
        raw_words = context.split()
        words_clean = [re.sub(r'[^\w]', '', w) for w in raw_words]
        
        # Find names and their word indices
        names_with_indices = []
        for idx, w in enumerate(words_clean):
            if NovelParser._is_valid_name(w):
                names_with_indices.append((w, idx))
                
        if not names_with_indices:
            return "Unknown"
            
        # Find speech verbs and their word indices
        verbs_with_indices = []
        for idx, w in enumerate(words_clean):
            w_lower = w.lower()
            if w_lower in SPEECH_VERBS:
                verbs_with_indices.append((w_lower, idx))
                
        # If we have both names and speech verbs, find the name closest to any verb
        if verbs_with_indices:
            best_name = None
            min_dist = 999
            for name, n_idx in names_with_indices:
                for verb, v_idx in verbs_with_indices:
                    dist = abs(n_idx - v_idx)
                    if dist < min_dist:
                        min_dist = dist
                        best_name = name
            
            # If a name is within 4 words of a speech verb, it's highly likely to be the speaker
            if best_name and min_dist <= 4:
                return best_name
                
        # Fallback: return the first valid name found
        return names_with_indices[0][0]

    @staticmethod
    def _estimate_demographics(name: str, full_text: str) -> Tuple[str, str]:
        """
        Guesses gender and age-group based on name and surrounding text context.
        Uses name databases, suffix heuristics, and contextual scanning.
        Returns (gender, age_group).
        """
        name_lower = name.lower()
        
        # 1. Determine age group using contextual keyword scanning
        age_group = "Mid-Age"
        
        senior_trig = ["old", "elderly", "aged", "grandfather", "grandmother", "grandpa", "grandma", 
                       "retired", "wrinkled", "grey", "gray", "senior", "ancient", "professor",
                       "uncle", "aunt", "mr.", "mrs.", "dr.", "lord", "lady", "sir ", "madam"]
                       
        young_trig = ["little", "young", "baby", "kid", "child", "boy", "girl", "son", 
                      "daughter", "school", "toy", "childhood", "infant", "toddler", "teenager", 
                      "youth", "pupil", "student", "play"]
                      
        # Explicit name checks first
        if any(w in name_lower for w in ["old", "elder", "grandfather", "grandmother", "professor"]):
            age_group = "Senior"
        elif any(w in name_lower for w in ["little", "young", "baby", "kid", "child"]):
            age_group = "Young"
        else:
            # Contextual scanning
            senior_score = 0
            young_score = 0
            pattern = re.compile(r'\b' + re.escape(name) + r'\b', re.IGNORECASE)
            matches = list(pattern.finditer(full_text))[:100]
            
            for m in matches:
                start = max(0, m.start() - 100)
                end = min(len(full_text), m.end() + 100)
                context = full_text[start:end].lower()
                
                for trig in senior_trig:
                    if trig in context:
                        senior_score += 1
                for trig in young_trig:
                    if trig in context:
                        young_score += 1
                        
            if senior_score > young_score and senior_score >= 1:
                age_group = "Senior"
            elif young_score > senior_score and young_score >= 1:
                age_group = "Young"
                
        # 2. Determine gender using database lookup + suffix heuristics
        gender = "Male"
        
        if name_lower in FEMALE_NAMES:
            gender = "Female"
        elif name_lower in MALE_NAMES:
            gender = "Male"
        elif name_lower.endswith(FEMALE_SUFFIXES):
            gender = "Female"
        elif name_lower.endswith(MALE_SUFFIXES):
            gender = "Male"
        elif name_lower.endswith(('aa', 'ee', 'ii', 'ri', 'ni', 'ti', 'hi', 'vi', 'li', 'si', 'mi', 'di', 'ki')):
            gender = "Female"
        elif name_lower.endswith(('sh', 'th', 'nd', 'rn', 'rk', 'rt', 'nk', 'nt')):
            gender = "Male"
        elif name_lower[-1] in ('a', 'i'):
            gender = "Female"
            
        return gender, age_group

    @staticmethod
    def _pick_default_vctk_voice(gender: str, age_group: str, char_index: int) -> str:
        """
        Picks a VCTK speaker ID to give each character a unique voice.
        Uses char_index to spread characters across different speakers.
        """
        # VCTK speaker pools by gender + age
        pools = {
            ("Female", "Young"):   ["0", "5", "8", "12", "17"],
            ("Female", "Mid-Age"): ["1", "3", "6", "9", "15", "20"],
            ("Female", "Senior"):  ["2", "10", "22"],
            ("Male", "Young"):     ["40", "44", "47", "50", "55"],
            ("Male", "Mid-Age"):   ["41", "43", "45", "48", "52", "58"],
            ("Male", "Senior"):    ["42", "46", "56"],
        }
        
        pool = pools.get((gender, age_group), pools[("Female", "Mid-Age")])
        return pool[char_index % len(pool)]
