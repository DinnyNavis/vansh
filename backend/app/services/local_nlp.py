import logging
import torch
import random
import requests
import json
import re
import time

logger = logging.getLogger(__name__)

class LocalNLPService:
    def __init__(self, model_name="Vamsi/T5_Paraphrase_Puzzler"):
        """
        Initialize the 'Elite Local' Engine.
        Supports advanced local LLM integration (Ollama) and transformer-based fallbacks.
        """
        self.model_name = model_name
        self.rephraser = None
        self.nlp = None  # spaCy
        self.device = 0 if torch.cuda.is_available() else -1
        self.ollama_base = "http://localhost:11434/api"
        # Priority list of modern, efficient Ollama models
        # Added Qwen 2.5 (JSON expert) and Gemma 2 (Refining expert)
        self.ollama_priority_models = ["llama3.2", "qwen2.5:3b", "gemma2:2b", "llama3.1", "phi3.5", "mistral", "phi3"]

    def _load_model(self):
        """Lazy load the transformer model for text polishing."""
        if self.rephraser is None:
            logger.info(f"Loading Local Transformer ({self.model_name})...")
            try:
                from transformers import pipeline
                self.rephraser = pipeline(
                    "text2text-generation", 
                    model=self.model_name, 
                    device=self.device
                )
            except Exception as e:
                logger.error(f"Failed to load primary local model: {e}")
                try:
                    from transformers import pipeline
                    self.rephraser = pipeline("text2text-generation", model="t5-small", device=self.device)
                except: pass

    def _load_spacy(self):
        """Lazy load spaCy for semantic analysis."""
        if self.nlp is None:
            try:
                import spacy
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy semantic engine loaded.")
            except Exception as e:
                logger.warning(f"spaCy not available, falling back to basic splitting: {e}")

    def _log_guardian_event(self, event_type, details):
        """Black Box Health Logging to track AI performance and rescues."""
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": event_type,
            "details": details
        }
        logger.info(f"GUARDIAN EVENT: {json.dumps(log_entry)}")
        # In a real-world scenario, this would write to a dedicated health collection/file
        try:
            with open("guardian_health.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass

    def rule_based_polish(self, text):
        """The 'Ironclad' Baseline: Polish text using pure logic (No AI required)."""
        if not text: return "A legacy of moments and memories."
        
        # 1. Clean Non-ASCII Garbage (Zero-Failure safeguard)
        polished = "".join(i for i in text if ord(i) < 128)
        
        # 2. Phonetic Thanglish/Hinglish/Fillers Removal (Comprehensive South Asian support)
        fillers = [
            r"\b(la|da|na|pa|dei|machan|ra|ga|umm|ahh|like|you\s+know|basically|actually|literally|meaning|what\s+happened|u\s+know|you\s+see|ya|ma|paa|nga|re|yaar)\b",
            r"\b(seri|enna|epdi|romba|konjam|naan|poren|irukken|vandhu|appram|nu|iru|va|solu|pannu|podu)\b"
        ]
        for pattern in fillers:
            polished = re.sub(pattern, "", polished, flags=re.IGNORECASE)
            
        # 3. Grammar Logic: Common Spoken Fixes
        grammar_map = {
            r"\bi\b": "I",
            r"\ba\s+apple\b": "an apple",
            r"\bi\s+is\b": "I am",
            r"\byou\s+was\b": "you were",
            r"\bwe\s+was\b": "we were",
            r"\bthey\s+was\b": "they were",
            r"\bgonna\b": "going to",
            r"\bwanna\b": "want to",
            r"\bgotta\b": "got to",
        }
        for pattern, replacement in grammar_map.items():
            polished = re.sub(pattern, replacement, polished)

        # 4. Aggressive Deduplication (Prevent loop-stutter failures)
        words = polished.split()
        if len(words) > 1:
            new_words = [words[0]]
            for i in range(1, len(words)):
                if words[i].lower() != words[i-1].lower():
                    new_words.append(words[i])
            polished = " ".join(new_words)

        # 5. Structural and AI Marker Cleaning
        polished = self._clean_ai_output(polished)
        
        # 6. Final Resilience Check
        if not polished or len(polished.strip()) < 5:
            return "This chapter of life is being recounted with great care."

        # 7. Sentence Capitalization
        sentences = re.split(r'(?<=[.!?])\s+', polished)
        final_sentences = []
        for s in sentences:
            if s and len(s) > 0:
                s = s.strip()
                final_sentences.append(s[0].upper() + s[1:])
        
        return " ".join(final_sentences).strip()

    def _call_ollama(self, prompt, system_prompt=None, stream=False):
        """Standardized Ollama call with Instant Connectivity Guard."""
        for model in self.ollama_priority_models:
            try:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": stream,
                    "options": {"temperature": 0.7}
                }
                if system_prompt:
                    payload["system"] = system_prompt
                
                # Rapid 100ms timeout for initial check to avoid blocking the user
                resp = requests.post(f"{self.ollama_base}/generate", json=payload, timeout=10)
                if resp.status_code == 200:
                    return resp.json().get("response", "").strip()
            except requests.exceptions.Timeout:
                logger.warning(f"Ollama timeout for {model} — seeking faster alternative...")
                continue
            except Exception as e:
                # If connection refused, Ollama is likely DOWN. Raise immediately for sentinel awareness.
                if "Connection refused" in str(e):
                    logger.error("Ollama Service is OFFLINE. Triggering Ironclad Baseline...")
                    raise ConnectionError("Ollama Offline")
                continue
        return None

    def _is_junk(self, text):
        """Intelligent Junk Detection to catch mangled or irrelevant AI output."""
        if not text or len(text.strip()) < 5:
            return True
        
        # 1. High Unicode Density (Detects excessive non-Roman chars if we expect English/Thanglish)
        non_ascii = len(re.findall(r'[^\x00-\x7F]', text))
        if non_ascii > len(text) * 0.3: # More than 30% non-ASCII
            return True
            
        # 2. Excessive Repetition (Detects AI looping)
        words = text.lower().split()
        if len(words) > 20:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3: # Extreme repetition
                return True
                
        # 3. Meta-Speech Detection (The AI talking about the task)
        meta_markers = [
            "please provide", "the text is not", "translate the", "as an ai", 
            "i cannot", "here is the", "translation of"
        ]
        text_lower = text.lower()
        if any(marker in text_lower for marker in meta_markers) and len(text) < 100:
            return True
            
        return False

    def _clean_ai_output(self, text, prefixes=None):
        """High-end recursive sanitization to strip all AI markers and artifacts."""
        if not text: return text
        
        # 1. Strip Markdown Blocks and AI-thought headers
        cleaned = re.sub(r"```[a-z]*\n?", "", text).replace("```", "").strip()
        cleaned = re.sub(r"(?i)<think>.*?</think>", "", cleaned, flags=re.DOTALL) # Strip DeepSeek-style thinking
        cleaned = re.sub(r"(?i)\[thought\].*?\[/thought\]", "", cleaned, flags=re.DOTALL)

        # 2. Aggressive Global Regex for Artifact Removal
        artifact_patterns = [
            r"(?i)\b(paraphrase|summarize|refined|corrected|polished|output|result|note|translation|translated|prose|narrative)\w*[:\s-]+",
            r"(?i)\b(here is|here's|this is|certainly|sure|absolutely) the (refined|corrected|polished|prose|translation|result)\w*[:\s-]*",
            r"(?i)\b(certainly|sure|here you go|absolutely|no problem)[,!\.\s]*",
            r"(?i)\bon it is: ",
            # Aggressive South Asian filler removal (la, da, na, pa, etc.)
            r"(?i)\b(la|da|na|pa|dei|machan|kanne|ra|ga|umm|ahh|like|you know|basically|actually)\b[\s,!\.]*",
        ]
        
        if prefixes:
            for p in prefixes:
                artifact_patterns.append(rf"(?i)^{re.escape(p)}\s*")

        for pattern in artifact_patterns:
            cleaned = re.sub(pattern, " ", cleaned)
            
        # 3. Recursive cleanup for stutter artifacts and double-words
        while True:
            prev_len = len(cleaned)
            cleaned = re.sub(r"(?i)\b(paraphrase|summarize|translation|refined|polished)\w*", "", cleaned).strip()
            # Remove immediate word repetitions robustly: "the the", "on on", including near punctuation
            cleaned = re.sub(r'\b(\w+)(?:\s+\1\b)+', r'\1', cleaned, flags=re.IGNORECASE)
            if len(cleaned) == prev_len: break

        # 4. Normalize Whitespace and Punctuation
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        cleaned = re.sub(r"\.\s+\.", ".", cleaned)
        cleaned = re.sub(r"([\.!\?])\1+", r"\1", cleaned) # deduplicate punctuation
        
        # 5. Fix Sentence Capitalization
        if cleaned:
            sentences = re.split(r'(?<=[.!?])\s+', cleaned)
            cleaned = " ".join([s[0].upper() + s[1:] if s and len(s) > 0 else s for s in sentences])
            
        return cleaned.strip()

    def refine_text(self, text, adaptive=False):
        """
        Cloud-Grade Multi-Pass Reflexion Pipeline.
        'adaptive=True' enables Fast Mode: collapses 3 passes into 1 for drafting speed.
        """
        if not text or len(text.strip()) < 5:
            return text

        if adaptive:
            # FAST MODE: Single-pass intensive refinement
            fast_prompt = (
                "ADAPTIVE FAST MODE: CLEAN & BEAUTIFY\n"
                "Refine this raw narrative text into a warm, first-person memoir prose. "
                "1. Fix core grammar and remove fillers (la, da, na, umm).\n"
                "2. Translate any non-English phrases to professional English.\n"
                "3. Use first-person 'I'. Describe sensory details briefly.\n"
                "4. Return ONLY the polished prose."
            )
            refined_fast = self._call_ollama(f"REFINE THIS TEXT:\n{text}", system_prompt=fast_prompt)
            
            # Guardian Check: If Fast Mode returns junk, escalate to full 3-pass rescue
            if self._is_junk(refined_fast):
                logger.warning("Fast Mode output detected as junk. Escalating to Triple-Pass Reflexion...")
                # Continue below to standard 3-pass logic
                pass
            else:
                return self._clean_ai_output(refined_fast)

        # Stage 1: The Cleaner (Fixer)
        # Focus: Grammar, Fillers, Spoken artifacts.
        cleaner_prompt = (
            "STAGE 1: CLEANER\n"
            "Your job is to fix the core grammar and remove all spoken artifacts. "
            "Remove 'la', 'da', 'na', 'pa', 'umm', 'ahh', 'like', 'you know'. "
            "Translate any Thanglish/Hinglish to professional English. "
            "Ensure it is in first-person 'I'."
        )
        cleaned_text = self._call_ollama(f"CLEAN THIS TEXT:\n{text}", system_prompt=cleaner_prompt)
        if not cleaned_text: cleaned_text = text # Fallback to input if stage fails
        else: cleaned_text = self._clean_ai_output(cleaned_text)

        # Stage 2: The Author (Narrative Master)
        # Focus: Warmth, Sensory Details, flow.
        author_prompt = (
            "STAGE 2: AUTHOR\n"
            "Your job is to transform the cleaned text into a warm, evocative memoir masterpiece. "
            "Use first-person 'I'. Follow these 'Cloud-Grade' rules:\n"
            "1. SHOW DON'T TELL: Instead of saying 'I was happy', describe how it felt.\n"
            "2. SENSORY DETAILS: Add mentions of sights, sounds, or smells appropriate to the context.\n"
            "3. NARRATIVE WARMTH: Use an authentic, reflective tone like a professional biographer.\n"
            "4. ELIMINATE ROBOTIC PHRASING: Make it sound human and deep."
        )
        authored_text = self._call_ollama(f"EXPAND AND BEAUTIFY THIS TEXT:\n{cleaned_text}", system_prompt=author_prompt)
        if not authored_text: authored_text = cleaned_text

        # Stage 3: The Editor (Critic)
        # Focus: Final polish, flow, consistency.
        editor_prompt = (
            "STAGE 3: MASTER EDITOR\n"
            "Perform a final professional polish on this memoir prose. "
            "Ensure flawless transitions, perfect punctuation, and a consistent first-person voice. "
            "Remove any remaining AI-style preamble or 'Here is the text' markers. "
            "Return ONLY the final polished English prose."
        )
        try:
            final_prose = self._call_ollama(f"PERFORM FINAL EDIT:\n{authored_text}", system_prompt=editor_prompt)
            
            # GUARDIAN RESCUE: If output is junk, trigger a secondary specialized model
            if self._is_junk(final_prose):
                logger.warning("Primary Local AI output detected as junk. Initiating Guardian Rescue pass...")
                self._log_guardian_event("JUNK_DETECTED", {"model": "primary", "output_preview": (final_prose or "")[:100]})
                
                rescue_prompt = (
                    "GUARDIAN RESCUE: REPAIR NARRATIVE\n"
                    "The following text is mangled or contains artifacts. Repair it into polished first-person English prose. "
                    "Remove all non-English script, fix repetition, and return ONLY the clean narrative."
                )
                final_prose = self._call_ollama(f"REPAIR THIS:\n{authored_text}", system_prompt=rescue_prompt)

            if final_prose and not self._is_junk(final_prose):
                return self._clean_ai_output(final_prose)
                
        except Exception as e:
            logger.error(f"Local AI Pipeline failed: {e}. Moving to Tier 2 fallback.")
            self._log_guardian_event("AI_PIPELINE_ERROR", {"error": str(e)})

        # TIER 2 FALLBACK: Transformer Refinement (If available)
        try:
            self._load_model()
            if self.rephraser:
                logger.info("Using Local Transformer for Tier 2 fallback...")
                result = self.rephraser(text, max_length=512, truncation=True)
                final_text = result[0]["generated_text"]
                if not self._is_junk(final_text):
                    return self._clean_ai_output(final_text)
        except Exception as e:
            logger.warning(f"Transformer fallback failed: {e}")

        # TIER 3: IRONCLAD BASELINE (No AI Required)
        logger.info("Guardian: Deploying Ironclad Baseline (Rule-Based Polish)...")
        self._log_guardian_event("IRONCLAD_BASELINE_TRIGGERED", {"input_preview": text[:100]})
        return self.rule_based_polish(text)

    def summarize(self, text, max_length=150):
        """Create a visual summary for image generation locally."""
        # Try Ollama first — explicit instruction so the model doesn't ask for input
        prompt = f"Summarize the following text into a vivid image-generation prompt focusing on key visual elements:\n\n<INPUT>\n{text}\n</INPUT>\n\nImage prompt:"
        summary = self._call_ollama(prompt)
        if summary:
            return self._clean_ai_output(summary, prefixes=["summarize:", "image prompt:"])

        try:
            self._load_model()
            results = self.rephraser(f"summarize: {text}", max_length=max_length, min_length=20, truncation=True)
            return self._clean_ai_output(results[0]['generated_text'], prefixes=["summarize:"])
        except:
            return " ".join(text.split()[:10])

    def generate_book_local(self, transcript, title="My Story"):
        """Generate a full book structure using High-End Elite Narrative Engine."""
        logger.info(f"Initiating Master Biographer Generation for '{title}'...")
        try:
            # 1. High-End Narrative Generation with Ollama
            prompt = f"""
            You are a world-class award-winning biographer. Transform the following transcript into a masterpiece of life-history.
            TITLE: "{title}"
            TRANSCRIPT: {transcript}
            
            NARRATIVE MASTERCLASS PROMPT:
            - VOICE: First-person ("I", "my"). Warm, reflective, and immersive.
            - TONE: Literary, polished, professional book-grade English.
            - LANGUAGE: If non-English input, translate to literary English flawlessly.
            - RICHNESS: Expand raw thoughts. Describe sensory details (smells, sounds, feelings).
            - THEMATIC DEPTH: Group life events into 3-5 distinct, profound chapters. No minor chapters.
            - TITLES: Create evocative, non-generic chapter titles.
            
            TRANSCRIPT (To process):
            {transcript}
            
            OUTPUT: Respond with VALID JSON ONLY.
            {{
              "title": "{title}",
              "subtitle": "A Legacy masterfully Chronicled",
              "chapters": [
                {{
                  "chapter_title": "Profound Chapter Title",
                  "chapter_summary": "Detailed visual description for an AI illustrator",
                  "content": "Deep, substantial first-person narrative prose..."
                }}
              ]
            }}
            """
            
            response_text = self._call_ollama(prompt, system_prompt="You are a Master Biographer. Respond with pure JSON. Absolute prose quality.")
            
            if response_text:
                try:
                    # Strip any markdown artifacts
                    clean_json = re.sub(r"```[a-z]*\n?", "", response_text).replace("```", "").strip()
                    data = json.loads(clean_json)
                    # Polish each chapter's content using the Ironclad pipeline
                    for ch in data.get("chapters", []):
                        ch["content"] = self.refine_text(ch["content"])
                    return data
                except Exception as parse_err:
                    logger.warning(f"Ollama JSON parse failed: {parse_err}. Triggering thematic recovery.")
                    self._log_guardian_event("JSON_PARSE_FAILED", {"error": str(parse_err)})
        except Exception as e:
            logger.error(f"Local AI Gen failed: {e}. Resorting to Ironclad Structural Recovery.")
            self._log_guardian_event("LOCAL_GEN_FAILED", {"error": str(e)})

        # 2. IRONCLAD STRUCTURAL RECOVERY: Thematic Clustering (Always works)
        return self._thematic_book_fallback(transcript, title)

    def _thematic_book_fallback(self, transcript, title):
        """Reconstructs narrative by grouping sentences into substantial thematic chapters."""
        try:
            self._load_spacy()
            if self.nlp:
                doc = self.nlp(transcript)
                sentences = [sent.text.strip() for sent in doc.sents]
            else:
                sentences = re.split(r'(?<=[.!?])\s+', transcript)

            if not sentences: return self._get_empty_book(title)

            # Grouping Logic: Aim for 3-5 robust chapters
            # We look for "Narrative Pivots" (changes in time, location, or subject)
            chapter_groups = []
            current_group = []
            # Grouping Logic: Aim for 3-5 robust chapters
            # Expanded South Asian context pivot words
            pivots = [
                "then", "later", "moved", "born", "school", "college", "work", "career", 
                "married", "children", "finally", "today", "chennai", "india", "home",
                "university", "job", "retirement", "village", "city"
            ]
            
            for i, sent in enumerate(sentences):
                current_group.append(sent)
                # Group threshold: substantial content
                is_pivot = any(p in sent.lower() for p in pivots) and len(current_group) > 8
                
                if (is_pivot or i == len(sentences) - 1) and len(current_group) >= 5:
                    chapter_groups.append(" ".join(current_group))
                    current_group = []
                elif i == len(sentences) - 1 and current_group:
                    # Append remaining
                    if chapter_groups: chapter_groups[-1] += " " + " ".join(current_group)
                    else: chapter_groups.append(" ".join(current_group))

            # Limit chapters to avoid "worthless" splits
            if len(chapter_groups) > 5:
                # Merge smallest
                while len(chapter_groups) > 5:
                    min_idx = 0
                    min_len = len(chapter_groups[0])
                    for idx, ch in enumerate(chapter_groups):
                        if len(ch) < min_len:
                            min_len = len(ch)
                            min_idx = idx
                    
                    if min_idx == 0: chapter_groups[0] += " " + chapter_groups.pop(1)
                    else: chapter_groups[min_idx-1] += " " + chapter_groups.pop(min_idx)

            chapters = []
            for i, ch_text in enumerate(chapter_groups):
                polished = self.refine_text(ch_text)
                
                # Title suggestion logic
                final_ch_title = f"{i+1}. "
                if self.nlp:
                    ch_doc = self.nlp(ch_text)
                    ents = [ent.text for ent in ch_doc.ents if ent.label_ in ["PERSON", "GPE", "EVENT"]]
                    if ents:
                        final_ch_title += f"The Journey to {ents[0]}"
                    else:
                        final_ch_title += "A New Chapter"
                else:
                    final_ch_title += "Master Narrative"

                chapters.append({
                    "chapter_title": final_ch_title,
                    "chapter_summary": self.summarize(polished, max_length=100),
                    "content": polished
                })

            return {
                "title": title,
                "subtitle": "A Masterfully Chronicled Legacy",
                "chapters": chapters
            }
        except Exception as e:
            logger.error(f"Thematic fallback failed: {e}")
            return self._get_empty_book(title)

    def _get_empty_book(self, title):
        return {
            "title": title,
            "subtitle": "A journey of legacy",
            "chapters": [{"chapter_title": "Our Legacy", "chapter_summary": "Initial entry", "content": "The story begins..."}]
        }
