"""
Image Generator Service — Supports OpenAI DALL-E 3, Gemini-powered Fallback, 
Lexica Search, AI Horde, and Local Styled Placeholders.
Ensures image generation works 100% of the time, even during total AI blackout.
"""

import os
import time
import logging
import requests
import urllib.parse
import uuid
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI
import google.generativeai as genai
from google.api_core import exceptions

logger = logging.getLogger(__name__)


class ImageGeneratorService:
    """Generates AI images for book chapters with a robust 5-tier failover stack."""

    def __init__(self, openai_api_key=None, gemini_api_key=None):
        self.openai_key = openai_api_key
        self.gemini_key = gemini_api_key
        self.openai_client = None
        self.gemini_model = None

        # Tier 1: OpenAI DALL-E 3
        if self.openai_key and self.openai_key.startswith("sk-"):
            try:
                self.openai_client = OpenAI(api_key=self.openai_key)
                logger.info("OpenAI DALL-E service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

        # Tier 2 Helper: Gemini for prompt optimization
        if self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
                # Discover latest available Flash models
                available_models = [m.name for m in genai.list_models() 
                                  if 'generateContent' in m.supported_generation_methods]
                
                priority = [
                    'models/gemini-2.0-flash',
                    'models/gemini-flash-latest',
                    'models/gemini-2.5-flash',
                    'models/gemini-pro-latest',
                ]
                
                self.model_name = None
                for p in priority:
                    if p in available_models:
                        self.model_name = p
                        break
                
                if not self.model_name:
                    self.model_name = available_models[0] if available_models else 'models/gemini-1.5-flash'
                
                logger.info(f"Using Gemini model for optimization: {self.model_name}")
                self.gemini_model = genai.GenerativeModel(self.model_name)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini optimizer: {e}")
                self.gemini_model = None

    def _safe_gemini_call(self, func, fallback_value=None, max_retries=3):
        """Execute a Gemini call with exponential backoff for 429/500 errors."""
        for attempt in range(max_retries + 1):
            try:
                return func()
            except (exceptions.ResourceExhausted, exceptions.InternalServerError, exceptions.ServiceUnavailable) as e:
                if attempt == max_retries:
                    logger.error(f"Gemini max retries reached in ImageGenerator: {e}")
                    return fallback_value
                
                wait_time = (2 ** attempt) + (random.random() * 2)
                logger.warning(f"Gemini error in ImageGenerator (attempt {attempt+1}/{max_retries+1}). Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
            except Exception as e:
                logger.error(f"Gemini unhandled error in ImageGenerator: {e}")
                return fallback_value
        return fallback_value

    def _get_visual_prompt_via_gemini(self, text):
        """Use Gemini to create a safe, descriptive visual prompt for biography illustrations."""
        if not self.gemini_model:
            return " ".join(text.split()[:5])

        prompt = f"""
        Analyze this biography story snippet and extract 4 or 5 descriptive visual elements.
        Format as adjective-noun pairs or nouns.
        Ensure the elements are professional and suitable for a family biography book.
        Avoid any sensitive or potentially restricted keywords.
        Example Input: "Grandpa finds a lost kitten in the rainy garden"
        Example Output: "Elderly man, rainy garden, small kitten, wooden fence"
        
        SUMMARY: {text}
        OUTPUT:"""

        def _call():
            response = self.gemini_model.generate_content(prompt)
            return response.text.strip().replace('"', '').replace('.', '')

        return self._safe_gemini_call(_call, fallback_value=" ".join(text.split()[:4]), max_retries=4)

    def _generate_via_lexica(self, prompt):
        """Tier 3: Search Lexica.art for a pre-generated high-quality image."""
        try:
            logger.info(f"Searching Lexica.art for: {prompt}")
            url = f"https://lexica.art/api/v1/search?q={urllib.parse.quote(prompt)}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                images = data.get("images", [])
                if images:
                    # Pick a random one from top 5 for variety
                    img = random.choice(images[:5])
                    return img.get("src")
            return None
        except Exception as e:
            logger.warning(f"Lexica search failed: {e}")
            return None

    def _generate_via_aihorde(self, prompt):
        """Tier 4: Use community-powered AI Horde (Slow but reliable)."""
        api_url = "https://aihorde.net/api/v2/generate/async"
        payload = {
            "prompt": f"{prompt}, cinematic lighting, photorealistic, 8k",
            "params": {
                "n": 1, "steps": 20, "width": 512, "height": 512, "sampler_name": "k_euler_a"
            },
            "nsfw": False,
            "models": ["stable_diffusion"]
        }
        headers = {"apikey": "0000000000", "Client-Agent": "VanshLegacy:1.0:antigravity"}
        
        try:
            logger.info("Engaging AI Horde Cluster...")
            r = requests.post(api_url, json=payload, headers=headers, timeout=20)
            if r.status_code == 202:
                job_id = r.json().get("id")
                for i in range(10): # Poll for 50 seconds max
                    time.sleep(5)
                    check = requests.get(f"https://aihorde.net/api/v2/generate/check/{job_id}", headers=headers)
                    if check.status_code == 200 and check.json().get("done"):
                        status = requests.get(f"https://aihorde.net/api/v2/generate/status/{job_id}", headers=headers)
                        if status.status_code == 200:
                            img_url = status.json().get("generations", [{}])[0].get("img")
                            if img_url: return img_url
            return None
        except Exception as e:
            logger.warning(f"AI Horde failed: {e}")
            return None

    def _generate_local_placeholder(self, title, save_path):
        """Tier 5: Final Failsafe - Generate a beautiful local styled placeholder."""
        try:
            logger.info(f"Generating local artistic placeholder for: {title}")
            width, height = 1024, 1024
            
            # Generate a consistent color based on title hash
            import hashlib
            h = int(hashlib.md5(title.encode()).hexdigest(), 16)
            hue = h % 360
            
            # Create a sophisticated color palette
            # bg_color = tuple(int(x) for x in Image.new("HSV", (1,1), (hue, 40, 30)).convert("RGB").getpixel((0,0)))
            # Simplified RGB derivation for resilience
            def hsv_to_rgb(h, s, v):
                import colorsys
                return tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h/360.0, s/100.0, v/100.0))
            
            bg_color = hsv_to_rgb(hue, 30, 20)
            accent_color = hsv_to_rgb(hue, 50, 70)
            
            img = Image.new('RGB', (width, height), color=bg_color)
            draw = ImageDraw.Draw(img)
            
            # Draw abstract patterns
            random.seed(h)
            for _ in range(15):
                shape = random.choice(["circle", "line", "rect"])
                x1, y1 = random.randint(0, width), random.randint(0, height)
                x2, y2 = random.randint(0, width), random.randint(0, height)
                opacity = random.randint(20, 60)
                col = accent_color + (opacity,)
                
                # Draw on a temp layer for opacity
                overlay = Image.new('RGBA', (width, height), (0,0,0,0))
                over_draw = ImageDraw.Draw(overlay)
                if shape == "circle":
                    r = random.randint(50, 200)
                    over_draw.ellipse([x1-r, y1-r, x1+r, y1+r], fill=col)
                elif shape == "line":
                    over_draw.line([x1, y1, x2, y2], fill=col, width=random.randint(1, 5))
                else:
                    over_draw.rectangle([x1, y1, x2, y2], outline=col, width=2)
                
                img.paste(overlay, (0,0), overlay)

            # Draw a subtle legacy-style border
            border_margin = 60
            draw.rectangle([border_margin, border_margin, width-border_margin, height-border_margin], outline=accent_color, width=3)
            
            # Text rendering
            try:
                # Preferred font: Georgia
                font = ImageFont.truetype("georgia.ttf", 65)
                sub_font = ImageFont.truetype("georgia.ttf", 35)
            except:
                try:
                    font = ImageFont.load_default().font_variant(size=60)
                    sub_font = ImageFont.load_default().font_variant(size=30)
                except:
                    font = ImageFont.load_default()
                    sub_font = ImageFont.load_default()

            text = title if title else "Legacy Illustration"
            if len(text) > 40: text = text[:37] + "..."
            
            # Draw Title in center with shadow
            draw.text((width/2 + 3, height/2 - 17), text, fill=(0, 0, 0, 100), font=font, anchor="mm")
            draw.text((width/2, height/2 - 20), text, fill=(245, 245, 245), font=font, anchor="mm")
            
            footer_text = "Artistic Legacy Representation"
            draw.text((width/2, height/2 + 80), footer_text, fill=accent_color, font=sub_font, anchor="mm")
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            img.save(save_path, "JPEG", quality=92)
            return True
        except Exception as e:
            logger.error(f"Artistic placeholder generation failed: {e}")
            # Absolute bottom fallback: Solid color
            try:
                img = Image.new('RGB', (1024, 1024), color=(50, 50, 50))
                img.save(save_path, "JPEG")
                return True
            except: return False

    def generate_chapter_image(self, chapter_summary, style="documentary"):
        """
        Highest Resilience Generation: DALL-E 3 -> Pollinations -> Lexica -> AI Horde -> Placeholder
        """
        chapter_title = chapter_summary[:30] # Used for placeholder if needed

        # 1. Primary: OpenAI DALL-E 3
        if self.openai_client:
            try:
                logger.info("Attempting DALL-E 3...")
                # Rich, biography-focused prompt for DALL-E
                dalle_prompt = f"A beautiful, high-quality {style} illustration for a family biography book: {chapter_summary}. Cinematic lighting, emotional depth, historical setting, professional artistic style, no text."
                response = self.openai_client.images.generate(
                    model="dall-e-3", prompt=dalle_prompt, size="1024x1024", quality="standard", n=1
                )
                return {"url": response.data[0].url, "source": "openai"}
            except Exception as e:
                logger.warning(f"DALL-E 3 skipped/failed: {e}")

        # 2. Backup: Gemini Optimized + Pollinations
        visual_prompt = self._get_visual_prompt_via_gemini(chapter_summary)
        # Add safety and style context to the prompt
        safe_full_prompt = f"Professional biography illustration of {visual_prompt}. High-quality, historical setting, artistic, family suitable, no text."
        encoded = urllib.parse.quote(safe_full_prompt)
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={uuid.uuid4().hex[:6]}"
        
        try:
            logger.info("Checking Pollinations stability...")
            head = requests.head(pollinations_url, timeout=5)
            if head.status_code == 200 and "image" in head.headers.get("Content-Type", ""):
                return {"url": pollinations_url, "source": "pollinations", "visual_prompt": visual_prompt}
        except: pass

        # 3. Teritary: Lexica Search (Pre-generated high quality)
        # Use slightly broader query for Lexica to ensure a hit
        lexica_query = f"biography book illustration {visual_prompt}"
        lexica_url = self._generate_via_lexica(lexica_query)
        if lexica_url:
            return {"url": lexica_url, "source": "lexica", "visual_prompt": visual_prompt}

        # 4. Quaternary: AI Horde (Slow but works)
        horde_url = self._generate_via_aihorde(visual_prompt)
        if horde_url:
            return {"url": horde_url, "source": "aihorde", "visual_prompt": visual_prompt}

        # 5. Final Stand: Local Placeholder Signal
        return {"url": "LOCAL_PLACEHOLDER", "source": "placeholder", "visual_prompt": chapter_title}

    def download_image(self, url, save_path, retries=5):
        """
        Download with strict validation and fallback to local placeholder on failure.
        """
        if url == "LOCAL_PLACEHOLDER":
            self._generate_local_placeholder("Chapter Illustration", save_path)
            return save_path

        headers = {"User-Agent": f"VanshLegacyBot/1.0 (Mozilla/121.0; {uuid.uuid4().hex[:4]})"}
        current_url = url
        
        for attempt in range(retries):
            try:
                logger.info(f"Downloading (Attempt {attempt+1}/{retries}) from {current_url[:40]}...")
                
                # Failover domain for pollinations
                if attempt == 2 and "pollinations.ai" in current_url:
                    if "image.pollinations" in current_url:
                        current_url = current_url.replace("image.pollinations.ai/prompt/", "pollinations.ai/p/")
                    else:
                        current_url = current_url.replace("pollinations.ai/p/", "image.pollinations.ai/prompt/")

                response = requests.get(current_url, timeout=40, headers=headers, stream=True)
                if response.status_code == 530: raise Exception("530 Provider Overload")
                response.raise_for_status()

                # Content Type Check
                ctype = response.headers.get("Content-Type", "").lower()
                if "image" not in ctype: raise ValueError(f"Invalid content: {ctype}")

                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                # Read first chunk for Magic Number validation
                chunks = response.iter_content(chunk_size=16384)
                first_chunk = next(chunks, None)
                if not first_chunk: raise ValueError("Empty response")

                # Validate JPEG/PNG/WebP headers
                valid_headers = [b"\xff\xd8", b"\x89PNG", b"RIFF"] # JPEG, PNG, WebP
                if not any(first_chunk.startswith(h) for h in valid_headers):
                    raise ValueError("Binary validation failed: Not a valid image header")

                with open(save_path, "wb") as f:
                    f.write(first_chunk)
                    for chunk in chunks: f.write(chunk)

                if os.path.getsize(save_path) < 2000: raise ValueError("File too small")

                logger.info(f"Successfully saved image: {save_path}")
                return save_path
                
            except Exception as e:
                logger.warning(f"Download attempt {attempt+1} failed: {e}")
                time.sleep(2 * (attempt + 1))

        # FINAL FALLBACK: If all downloads fail, generate the placeholder
        logger.error("All image downloads failed. Falling back to local styled placeholder.")
        self._generate_local_placeholder("Illustration", save_path)
        return save_path
