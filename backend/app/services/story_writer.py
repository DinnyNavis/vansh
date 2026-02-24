"""
Story Writer Service — Refines text and generates full book chapters using Google Gemini (Free Tier).
"""

import json
import logging
import re
import time
import random
from openai import OpenAI
import google.generativeai as genai
from google.api_core import exceptions
from .local_nlp import LocalNLPService

logger = logging.getLogger(__name__)

class StoryWriterService:
    def __init__(self, gemini_api_key, openai_api_key=None):
        self.gemini_api_key = gemini_api_key
        self.openai_api_key = openai_api_key
        self.openai_client = None
        self.local_nlp = LocalNLPService()
        
        if not self.openai_api_key:
            logger.warning("OpenAI API Key is missing. Book generation will rely on Gemini or Local NLP.")
        
        # Initialize OpenAI (NOW PRIMARY)
        if self.openai_api_key and self.openai_api_key.startswith("sk-"):
            try:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                logger.info("OpenAI service initialized as PRIMARY")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

        # Initialize Gemini as FALLBACK
        try:
            if self.gemini_api_key:
                genai.configure(api_key=self.gemini_api_key)
                # Dynamically discover available models
                try:
                    self.available_gemini_models = [m.name for m in genai.list_models() 
                                                  if 'generateContent' in m.supported_generation_methods]
                except Exception as list_err:
                    logger.warning(f"Failed to list Gemini models: {list_err}")
                    self.available_gemini_models = []
                
                # Order of preference based on confirmed available models
                self.priority_models = [
                    'models/gemini-2.0-flash',
                    'models/gemini-flash-latest',
                    'models/gemini-2.5-flash',
                    'models/gemini-2.0-flash-lite',
                    'models/gemini-pro-latest',
                ]
                
                self.model_name = None
                for p in self.priority_models:
                    if p in self.available_gemini_models:
                        self.model_name = p
                        break
                
                if not self.model_name:
                    self.model_name = self.available_gemini_models[0] if self.available_gemini_models else 'models/gemini-1.5-flash'
                
                logger.info(f"Fallback Gemini model: {self.model_name}")
                self.model = genai.GenerativeModel(self.model_name)
            else:
                self.model = None
                self.model_name = None
            
        except Exception as e:
            logger.error(f"Gemini initialization error: {e}")
            self.model_name = 'models/gemini-1.5-flash'
            self.model = genai.GenerativeModel(self.model_name)
            self.available_gemini_models = [self.model_name]

    def refine_text(self, raw_text, retry_callback=None):
        """Refine raw user input for professional book-grade grammar and flow."""
        # NOTE: RAW INPUT is placed first and starred so the LLM cannot possibly miss it.
        prompt = f"""TASK: Refine the following raw text into polished English prose.

RAW INPUT TEXT:
***
{raw_text}
***

YOU ARE: An elite book editor, polyglot, and South Asian language specialist.
DO NOT ask for input. DO NOT say 'please provide'. The text is ALREADY given above between the *** markers.

STRICT RULES:
1. CRYSTAL CLEAR FIDELITY (PRIMARY):
   - Preserve EVERY single fact, name, place, date, and specific detail.
   - Do not generalize. Do not summarize. Do not abbreviate.
   - If the user says 'I saw a red car', do not change it to 'a vehicle'.
2. LANGUAGE DETECTION & CODE-SWITCHING:
   - Input may be English, Tamil, Hindi, Thanglish (e.g. 'naan school poren'),
     Hinglish, or any mix of South Asian + English languages.
   - Translate all non-English parts into PROFESSIONAL, VIVID English while keeping the EXACT original meaning.
3. GRAMMAR & FLOW:
   - Fix all errors, spelling, punctuation.
   - Smooth the transitions so it reads like a high-end published memoir.
4. FILLER REMOVAL: Remove 'umm', 'ahh', 'like', 'you know', 'basically' only if they add ZERO value.
5. FIRST PERSON: Write exclusively as 'I'. Never change narrative voice.
6. OUTPUT: Return ONLY the refined English prose. No labels or preamble.

REFINED CRYSTAL-CLEAR PROSE:"""

        META_RESPONSE_PHRASES = [
            "please provide", "provide the text", "provide the raw",
            "what would you like", "i need the text", "kindly share",
            "once you provide", "once the input",
        ]

        def _openai_call():
            if not self.openai_client: raise Exception("OpenAI not available")
            logger.info("Using OpenAI (PRIMARY) for text refinement...")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": (
                        "You are an elite book editor and South Asian language specialist. "
                        "Refine the provided text into polished English memoir prose. "
                        "Handle Thanglish, Hinglish, and any language mix. "
                        "Fix all grammar, remove fillers. Keep first-person voice. "
                        "Return ONLY the refined prose."
                    )},
                    {"role": "user", "content": f"Refine this text:\n\n{raw_text}"}
                ]
            )
            result = response.choices[0].message.content.strip()
            if any(p in result.lower() for p in META_RESPONSE_PHRASES) or self.local_nlp._is_junk(result):
                raise Exception("OpenAI returned poor quality response")
            return self.local_nlp._clean_ai_output(result)

        def _gemini_fallback(model=None):
            if not self.model: raise Exception("Gemini not available")
            logger.info("Using Gemini (FALLBACK) for text refinement...")
            m = model if model else self.model
            response = m.generate_content(prompt)
            result = response.text.strip()
            
            # GUARDIAN VALIDATION: Check for meta-responses or junk
            if any(p in result.lower() for p in META_RESPONSE_PHRASES) or self.local_nlp._is_junk(result):
                logger.warning("Gemini returned meta-response or junk, forcing fallback")
                raise Exception("Poor quality cloud response detected")
                
            return self.local_nlp._clean_ai_output(result)

        def _local_fallback():
            logger.info("Guardian Rescue: Using Local NLP for final high-resilience polish...")
            return self.local_nlp.refine_text(raw_text, adaptive=False)

        return self._safe_ai_call(_openai_call, gemini_fallback=_gemini_fallback, local_fallback=_local_fallback, default_value=raw_text, retry_callback=retry_callback, max_retries=2)

    def _safe_ai_call(self, openai_func, gemini_fallback=None, local_fallback=None, default_value=None, retry_callback=None, max_retries=2):
        """Execute AI call with OpenAI as PRIMARY and Gemini/Local as fallbacks."""
        used_models = {self.model_name}
        
        # 1. Primary: OpenAI
        if self.openai_client:
            try:
                return openai_func()
            except Exception as e:
                logger.warning(f"OpenAI primary failed: {e}")
                if retry_callback: retry_callback(88, 0) # Signal switch to fallback

        # 2. Secondary: Gemini (Fallback)
        if self.model and gemini_fallback:
            used_models = {self.model_name}
            for attempt in range(max_retries):
                try:
                    logger.info(f"Using Gemini fallback (attempt {attempt+1})...")
                    return gemini_fallback()
                except (exceptions.ResourceExhausted, exceptions.InternalServerError, exceptions.ServiceUnavailable) as e:
                    logger.warning(f"Gemini {self.model_name} busy on attempt {attempt+1}: {e}")
                    
                    next_model_name = None
                    for p in self.priority_models:
                        if p in self.available_gemini_models and p not in used_models:
                            next_model_name = p
                            break
                    
                    if next_model_name:
                        logger.info(f"Shuffling to alternate Gemini model: {next_model_name}")
                        used_models.add(next_model_name)
                        temp_model = genai.GenerativeModel(next_model_name)
                        try:
                            return gemini_fallback(model=temp_model)
                        except Exception as inner_e:
                            logger.warning(f"Shuffled model {next_model_name} also failed: {inner_e}")
                    
                    if attempt < max_retries - 1:
                        wait_time = 0.5 + random.random()
                        time.sleep(wait_time)
                except Exception as e:
                    logger.error(f"Gemini critical error: {e}")
                    break
        
        # 3. Final Local Fallback
        if local_fallback:
            try:
                logger.info("Cloud APIs failed. Using Local legacy generation...")
                if retry_callback: retry_callback(77, 0) # Local fallback
                return local_fallback()
            except Exception as loc_err:
                logger.error(f"Local fallback failed: {loc_err}")
        
        return default_value

    def generate_book(self, transcript, title="My Story", retry_callback=None):
        """Generate a full book structure from a transcript with Master Biographer storytelling."""
        
        # Zero-Failure: If transcript is extremely short, treat it as a seed and expand
        if len(transcript.strip().split()) < 30:
            logger.info("Short transcript detected. Engaging Seed Expansion mode...")
            transcript = f"The following memory is the seed of a legacy: {transcript}. Bloom this short memory into a substantial, multi-chapter narrative chronicling the depth hidden within these few words."

        prompt = f"""
        You are an award-winning world-class biographer and South Asian language specialist.
        Transform the following transcript into a profound, detailed first-person memoir.
        BOOK TITLE: "{title}"
        
        NARRATIVE VISION:
        1. MASTER PROSE: Use rich, evocative language in English. Describe sensory details—not just what happened, but what it felt like.
        2. MULTILINGUAL & CODE-SWITCHING SUPPORT:
           - The transcript may be in ANY language or mix: English, Tamil, Hindi, Thanglish (Tamil words typed or spoken in Roman/English script), Hinglish, or any regional blend.
           - Examples of Thanglish you must understand: "naan Chennai-la valarndhen", "amma konjam strict-a irupaanga", "ippo naan engineer aayitten".
           - Understand the full meaning from context regardless of language mix. Generate the ENTIRE book in professional English only.
        3. FIRST-PERSON VOICE: Write exclusively as "I". Reflective, warm, and authentic.
        4. STRUCTURAL DEPTH: Break the story into 3-5 PROFOUND chapters. Avoid short, worthless chapters.
        5. STORY ARC: Follow a clear narrative journey from orientation to reflection.
        6. ZERO ARTIFACTS: Return ONLY the narrative prose in JSON. No AI prefixes.
        
        TRANSCRIPT:
        {transcript}

        OUTPUT FORMAT: Respond ONLY with valid JSON.
        {{
          "title": "{title}",
          "subtitle": "A Legacy Masterfully Chronicled",
          "chapters": [
            {{
              "chapter_title": "Evocative Chapter Title (e.g. 'The Echoes of Youth')",
              "chapter_summary": "Detailed visual description for an AI illustrator",
              "content": "Professional, substantial narrative prose written for a published book..."
            }}
          ]
        }}
        """

        def _openai_call():
            if not self.openai_client: raise Exception("OpenAI not available")
            logger.info("Using OpenAI (PRIMARY) for book generation...")
            if retry_callback: retry_callback(99, 0)
                
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": (
                        "You are a world-class biographer and polyglot. Write grammatically flawless, "
                        "first-person biographical prose in professional English. "
                        "If the input is not English, translate it to English automatically. "
                        "Zero filler words, zero grammar errors. "
                        "Respond with valid JSON only."
                    )},
                    {"role": "user", "content": prompt}
                ]
            )
            return json.loads(response.choices[0].message.content)

        def _gemini_fallback(model=None):
            if not self.model: raise Exception("Gemini not available")
            logger.info("Using Gemini (FALLBACK) for book generation...")
            m = model if model else self.model
            try:
                response = m.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        response_mime_type="application/json",
                    )
                )
            except Exception as e:
                if "404" in str(e) or "not found" in str(e).lower():
                    logger.warning("Gemini Flash unavailable, falling back to gemini-pro...")
                    temp_model = genai.GenerativeModel('gemini-1.0-pro')
                    response = temp_model.generate_content(prompt)
                else:
                    raise e
            
            return self._parse_json_response(response.text)

        def _local_fallback():
            logger.info("Using Local NLP for book generation (Offline Mode)...")
            return self.local_nlp.generate_book_local(transcript, title=title)

        # Swapped Priority call
        result = self._safe_ai_call(_openai_call, gemini_fallback=_gemini_fallback, local_fallback=_local_fallback, retry_callback=retry_callback, max_retries=3)
        
        # FINAL IRONCLAD CHECK: If all else failed to produce a valid dict, force structural recovery
        if not result or not isinstance(result, dict) or "chapters" not in result:
            logger.error("All AI services failed to generate book JSON. Triggering Structural Recovery...")
            result = self.local_nlp.generate_book_local(transcript, title=title)
            
        return result

    def regenerate_chapter(self, transcript, chapter_title, context="", retry_callback=None):
        """Regenerate a specific chapter with deep fallbacks."""
        prompt = f"""
        Regenerate the chapter "{chapter_title}" based on the following story transcript.
        {context if context else ""}

        TRANSCRIPT:
        {transcript}

        Respond ONLY with the new chapter content as a plain string.
        """

        def _openai_call():
            if not self.openai_client: raise Exception("OpenAI not available")
            logger.info("Using OpenAI (PRIMARY) for chapter regeneration...")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional biographer."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()

        def _gemini_fallback(model=None):
            if not self.model: raise Exception("Gemini not available")
            logger.info("Using Gemini (FALLBACK) for chapter regeneration...")
            m = model if model else self.model
            response = m.generate_content(prompt)
            return response.text.strip()

        def _local_fallback():
            logger.info("Using Local NLP for chapter regeneration...")
            return self.local_nlp.refine_text(transcript) # Simple fallback

        return self._safe_ai_call(_openai_call, gemini_fallback=_gemini_fallback, local_fallback=_local_fallback, retry_callback=retry_callback)

    def _parse_json_response(self, text):
        """Clean and parse JSON from AI response with robust structural recovery."""
        body = text.strip()
        # Remove Markdown backticks if present
        if body.startswith("```json"): body = body[7:-3]
        elif body.startswith("```"): body = body[3:-3]
        body = body.strip()
        
        # Heuristic search for the first '{' and last '}' if parsing fails initially
        if not body.startswith("{"):
            start = body.find("{")
            end = body.rfind("}")
            if start != -1 and end != -1: body = body[start:end+1]
        
        try:
            data = json.loads(body)
            # Standardize and clean all narrative content
            if "chapters" in data:
                for ch in data["chapters"]:
                    if "content" in ch:
                        # Ensure content is cleaned of AI artifacts and polished
                        ch["content"] = self.local_nlp._clean_ai_output(ch["content"])
            return data
        except Exception as e:
            logger.error(f"Failed to parse AI JSON: {body[:200]}... Error: {e}")
            # Final attempt: try to fix common JSON errors (trailing commas, etc.)
            try:
                # Basic regex attempt to fix minor issues like trailing commas before closing braces
                fixed_body = re.sub(r",\s*([\]}])", r"\1", body)
                data = json.loads(fixed_body)
                return data
            except:
                raise e
