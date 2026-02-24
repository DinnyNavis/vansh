"""
Unguided Mode Routes — The core book generation pipeline.
Handles transcription, text processing, book generation, image generation, and PDF export.
"""

import os
import uuid
import logging
import threading
import concurrent.futures
from functools import wraps
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, decode_token
from werkzeug.utils import secure_filename

from ..models import ProjectModel
from ..extensions import socketio
from ..services.transcription import TranscriptionService
from ..services.story_writer import StoryWriterService
from ..services.image_generator import ImageGeneratorService
from ..services.pdf_generator import PDFGeneratorService
from ..services.video_processor import VideoProcessorService
from ..services.deepgram_service import DeepgramService
from ..services.cloudinary_service import CloudinaryService
from ..services.local_transcription import LocalTranscriptionService
from ..services.local_nlp import LocalNLPService
from ..services.docx_generator import DocxGeneratorService
from ..services.guardian import guardian
import random

logger = logging.getLogger(__name__)

unguided_bp = Blueprint("unguided", __name__)

# ── Service Singletons (lazy-initialized, cached) ─────────────
_story_writer = None
_image_generator = None
_local_nlp = None
_transcription_service = None


def _get_story_writer(app):
    """Get or create cached StoryWriterService singleton."""
    global _story_writer
    if _story_writer is None:
        _story_writer = StoryWriterService(
            app.config.get("GEMINI_API_KEY"),
            app.config.get("OPENAI_API_KEY")
        )
    return _story_writer


def _get_image_generator(app):
    """Get or create cached ImageGeneratorService singleton."""
    global _image_generator
    if _image_generator is None:
        _image_generator = ImageGeneratorService(
            openai_api_key=app.config.get("OPENAI_API_KEY"),
            gemini_api_key=app.config.get("GEMINI_API_KEY")
        )
    return _image_generator


def _get_local_nlp(app=None):
    """Get or create cached LocalNLPService singleton."""
    global _local_nlp
    if _local_nlp is None:
        _local_nlp = LocalNLPService()
    return _local_nlp


def _get_transcription_service(app):
    """Get or create cached TranscriptionService singleton."""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService(
            api_key=app.config.get("OPENAI_API_KEY")
        )
    return _transcription_service


def jwt_required_with_query():
    """Decorator that accepts JWT from Authorization header OR ?token= query param.
    This is needed for file download routes where the browser uses window.open()."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Try standard header first
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                # Let flask-jwt-extended handle it normally
                @jwt_required()
                def inner(*a, **kw):
                    return fn(*a, **kw)
                return inner(*args, **kwargs)

            # Fallback: check ?token= query param
            token = request.args.get("token")
            if not token:
                return jsonify({"error": "Missing authorization token"}), 401

            try:
                decode_token(token)
            except Exception as e:
                logger.warning(f"Token decode failed: {e}")
                return jsonify({"error": "Invalid or expired token"}), 401

            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ── Heartbeat Guard ───────────────────────────────────────────

class HeartbeatSender:
    """Helper to pulse progress updates during long AI tasks."""
    def __init__(self, project_id, stage, progress, message):
        self.project_id = project_id
        self.stage = stage
        self.progress = progress
        self.message = message
        self.stop_event = threading.Event()
        self.thread = None

    def __enter__(self):
        def _pulse():
            import time
            while not self.stop_event.wait(15):
                try:
                    _emit_progress(self.project_id, self.stage, self.progress, self.message)
                except: pass
        
        self.thread = threading.Thread(target=_pulse, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_event.set()
        # No need to join, it's a daemon and we want fast exit

def _emit_progress(project_id, stage, progress, message, data=None):
    """Emit real-time progress update via WebSocket."""
    project_id = str(project_id)
    payload = {
        "project_id": project_id,
        "stage": stage,
        "progress": progress,
        "message": message,
    }
    if data:
        payload["data"] = data
    
    logger.info(f"Emitting progress: project={project_id}, stage={stage}, msg={message}")
    socketio.emit("progress_update", payload, room=project_id)


def _allowed_file(filename, allowed_set):
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_set


# ============================================================
# AUDIO TRANSCRIPTION
# ============================================================

@unguided_bp.route("/transcribe", methods=["POST"])
@jwt_required()
def transcribe_audio():
    """Upload audio and transcribe using Whisper."""
    user_id = get_jwt_identity()

    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    file = request.files["audio"]
    project_id = request.form.get("project_id")

    if not project_id:
        return jsonify({"error": "project_id is required"}), 400

    if not _allowed_file(file.filename, current_app.config["ALLOWED_AUDIO_EXTENSIONS"]):
        return jsonify({"error": "Unsupported audio format"}), 400

    # Save file
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "audio")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}.{file.filename.rsplit('.', 1)[1].lower()}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    print(f"\n>>> [API] Received transcription request for project: {project_id}")
    print(f">>> [API] Audio saved to: {filepath} | Auto-generate: {request.form.get('auto_generate')}")

    auto_generate = request.form.get("auto_generate") == "true"
    app = current_app._get_current_object()

    # Transcribe in background thread
    def _transcribe():
        try:
            with app.app_context():
                _emit_progress(project_id, "transcribing", 10, "Starting transcription...")

                # Unified Transcription with OpenAI Primary + Local Fallback (Protected by Guardian)
                transcription_service = _get_transcription_service(app)
                result = guardian.safe_execute(
                    "transcription",
                    primary_func=lambda: transcription_service.transcribe(filepath),
                    fallback_func=lambda: LocalTranscriptionService().transcribe(filepath),
                    default_value={"text": "Transcription failed, please try writing your story."}
                )

                # Fetch project again inside thread to ensure DB connection is active
                project = ProjectModel.find_by_id(project_id)
                if not project:
                    logger.error(f"Project {project_id} not found during transcription.")
                    _emit_progress(project_id, "error", 0, "Project context lost.")
                    return

                raw_text = result["text"].strip()
                logger.info(f"Raw transcript ({result.get('source', 'unknown')} source): {raw_text[:100]}")

                # ── PHASE 1: Emit raw transcript IMMEDIATELY so user sees something ──
                # This makes the UI feel instant. Refinement is a bonus on top.
                _emit_progress(project_id, "transcribing", 90, "Transcription done — detecting language & polishing...", {
                    "raw_transcript": raw_text,
                })

                # ── PHASE 2: Refine in-place (Gemini → OpenAI → Local fallback) ──
                try:
                    def _retry_cb(attempt, wait):
                        if attempt == 88:
                            msg = "Cloud is busy, switching to secondary processor..."
                        elif attempt == 77:
                            msg = "Cloud services exhausted — engaging Private AI (Offline)..."
                        else:
                            msg = f"AI is busy, retrying in {wait}s (attempt {attempt})..."
                        _emit_progress(project_id, "transcribing", 95, msg)

                    writer = _get_story_writer(app)
                    with HeartbeatSender(project_id, "transcribing", 95, "Our AI is meticulously polishing your narrative..."):
                        refined = writer.refine_text(raw_text, retry_callback=_retry_cb)
                except Exception as ref_err:
                    logger.warning(f"Auto-refinement failed, using fast-mode local fallback: {ref_err}")
                    try:
                        service = _get_local_nlp(app)
                        refined = service.refine_text(raw_text, adaptive=True)
                    except:
                        refined = raw_text

                # Save both raw + refined to DB
                ProjectModel.update(project_id, {
                    "transcript": raw_text,
                    "refined_text": refined,
                    "status": "transcribed",
                })

                # Emit final refined transcript
                _emit_progress(project_id, "transcribed", 100, "Transcript polished and ready ✓", {
                    "transcript": refined,
                })

                if auto_generate:
                    # Delay slightly so user can see the "Transcript polished" state
                    import time
                    time.sleep(1.5)
                    _do_generate_book(app, project_id, refined, auto_images=True)

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            _emit_progress(project_id, "error", 0, f"Transcription failed: {str(e)}")
        finally:
            # Clean up
            try:
                os.remove(filepath)
            except OSError:
                pass

    socketio.start_background_task(_transcribe)
    return jsonify({"message": "Transcription started", "project_id": project_id}), 202



# ============================================================
# TEXT INPUT PROCESSING
# ============================================================

@unguided_bp.route("/process-text", methods=["POST"])
@jwt_required()
def process_text():
    """Process raw text input — refine grammar."""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    text = data.get("text", "").strip()
    project_id = data.get("project_id")
    auto_generate = data.get("auto_generate") == True

    print(f"\n>>> [API] Received process-text for project: {project_id}")

    if not text:
        return jsonify({"error": "Text is required"}), 400
    if not project_id:
        return jsonify({"error": "project_id is required"}), 400

    app = current_app._get_current_object()

    def _process():
        try:
            with app.app_context():
                logger.info(f"Starting background text refinement for project: {project_id}")
                _emit_progress(project_id, "refining", 10, "Refining your text...")

                # Safety check for project presence
                project = ProjectModel.find_by_id(project_id)
                if not project:
                    logger.error(f"Project {project_id} not found during text refinement.")
                    _emit_progress(project_id, "error", 0, "Project not found. Please restart from dashboard.")
                    return

                # ── PHASE 2: Refine in-place ──
                try:
                    def _retry_cb(attempt, wait):
                        if attempt == 88:
                            msg = "Cloud is busy, switching to secondary processor..."
                        elif attempt == 77:
                            msg = "Cloud services exhausted — engaging Private AI (Offline)..."
                        else:
                            msg = f"AI is busy, retrying in {wait}s (attempt {attempt})..."
                        _emit_progress(project_id, "refining", 10, msg)
                    
                    writer = _get_story_writer(app)
                    refined = writer.refine_text(text, retry_callback=_retry_cb)
                except Exception as api_err:
                    logger.warning(f"Gemini API failed, falling back to local NLP (Fast Mode): {api_err}")
                    service = _get_local_nlp(app)
                    refined = service.refine_text(text, adaptive=True)

                ProjectModel.update(project_id, {
                    "transcript": text,
                    "refined_text": refined,
                    "status": "transcribed",
                })

                _emit_progress(project_id, "transcribed", 100, "Text refined", {
                    "transcript": refined,
                })

                if auto_generate:
                    _do_generate_book(app, project_id, refined, auto_images=True)

        except Exception as e:
            logger.error(f"Text processing error: {e}")
            _emit_progress(project_id, "error", 0, f"Text processing failed: {str(e)}")

    socketio.start_background_task(_process)
    return jsonify({"message": "Text processing started"}), 202


# ============================================================
# VIDEO UPLOAD
# ============================================================

@unguided_bp.route("/upload-video", methods=["POST"])
@jwt_required()
def upload_video():
    """Upload video, extract audio, and transcribe."""
    user_id = get_jwt_identity()

    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    file = request.files["video"]
    project_id = request.form.get("project_id")

    if not project_id:
        return jsonify({"error": "project_id is required"}), 400

    if not _allowed_file(file.filename, current_app.config["ALLOWED_VIDEO_EXTENSIONS"]):
        return jsonify({"error": "Unsupported video format"}), 400

    # Save video
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "video")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}.{file.filename.rsplit('.', 1)[1].lower()}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    auto_generate = request.form.get("auto_generate") == "true"
    app = current_app._get_current_object()

    def _process_video():
        audio_path = None
        try:
            with app.app_context():
                _emit_progress(project_id, "extracting", 10, "Extracting audio from video...")

                # Extract audio
                video_service = VideoProcessorService()
                audio_path = video_service.extract_audio(filepath)

                _emit_progress(project_id, "transcribing", 30, "Transcribing audio...")

                with HeartbeatSender(project_id, "transcribing", 60, "Transcribing and extracting the essence of your video..."):
                    # Unified Transcription with OpenAI Primary + Local Fallback
                    transcription_service = _get_transcription_service(app)
                    result = guardian.safe_execute(
                        "video_transcription",
                        primary_func=lambda: transcription_service.transcribe(audio_path),
                        fallback_func=lambda: LocalTranscriptionService().transcribe(audio_path),
                        default_value={"text": "Transcription unavailable, but your video is safe."}
                    )

                _emit_progress(project_id, "transcribing", 90, "Video transcription complete. Polishing...")

                # Auto-Refine: Unified logic with Audio/Text paths
                try:
                    def _retry_cb(attempt, wait):
                        _emit_progress(project_id, "transcribing", 95, f"Refining narrative... (attempt {attempt})")
                    
                    writer = _get_story_writer(app)
                    refined = writer.refine_text(result["text"], retry_callback=_retry_cb)
                except Exception as ref_err:
                    logger.warning(f"Video refinement failed, falling back to local: {ref_err}")
                    try:
                        service = _get_local_nlp(app)
                        refined = service.refine_text(result["text"], adaptive=True)
                    except:
                        refined = result["text"]

                ProjectModel.update(project_id, {
                    "transcript": result["text"],
                    "refined_text": refined,
                    "status": "transcribed",
                })

                _emit_progress(project_id, "transcribed", 100, "Video processed and refined", {
                    "transcript": refined,
                })

                if auto_generate:
                    _do_generate_book(app, project_id, refined, auto_images=True)

        except Exception as e:
            logger.error(f"Video processing error: {e}")
            _emit_progress(project_id, "error", 0, f"Video processing failed: {str(e)}")
        finally:
            try:
                os.remove(filepath)
            except OSError:
                pass
            if audio_path:
                try:
                    os.remove(audio_path)
                except OSError:
                    pass

    socketio.start_background_task(_process_video)
    return jsonify({"message": "Video processing started"}), 202


# ============================================================
# BOOK GENERATION
# ============================================================

# Internal helper for chained generation
def _do_generate_book(app, project_id, transcript, auto_images=False):
    """Internal task logic for generating a book and optionally images."""
    try:
        with app.app_context():
            project = ProjectModel.find_by_id(project_id)
            if not project:
                logger.error(f"Project {project_id} not found for book generation fallback.")
                _emit_progress(project_id, "error", 0, f"Auto-generation failed: Project context lost (ID: {project_id})")
                return

            _emit_progress(project_id, "writing", 10, "Writing your story...")

            def _retry_cb(attempt, wait):
                if attempt == 88:
                    msg = "Cloud is busy, switching to secondary processor..."
                elif attempt == 77:
                    msg = "Cloud services exhausted — engaging Private AI (Offline)..."
                else:
                    msg = f"AI is busy, retrying in {wait}s (attempt {attempt})..."
                _emit_progress(project_id, "writing", 10, msg)

            writer = _get_story_writer(app)
            # Tiered Guardian Execution: OpenAI -> Gemini -> Local AI -> Ironclad Thematic Cluster
            with HeartbeatSender(project_id, "writing", 40, "Crafting the chapters of your legacy..."):
                book_data = guardian.safe_execute(
                    "book_generation",
                    primary_func=lambda: writer.generate_book(
                        transcript,
                        title=project.get("title", "My Story"),
                        retry_callback=_retry_cb
                    ),
                    fallback_func=lambda: _get_local_nlp(app).generate_book_local(
                        transcript, 
                        title=project.get("title", "My Story")
                    ),
                    default_value={
                        "title": project.get("title", "My Story"),
                        "chapters": [{"chapter_title": "My Legacy", "content": transcript}]
                    }
                )

            _emit_progress(project_id, "writing", 70, "Book structure complete")

            chapters = []
            for idx, ch in enumerate(book_data.get("chapters", [])):
                chapter = {
                    "id": str(uuid.uuid4()),
                    "chapter_title": ch.get("chapter_title", f"Chapter {idx + 1}"),
                    "chapter_summary": ch.get("chapter_summary", ""),
                    "content": ch.get("content", ""),
                    "image_url": None,
                    "image_type": None,
                    "locked": False,
                }
                chapters.append(chapter)
                _emit_progress(project_id, "chapter_ready", int(70 + (25 * (idx + 1) / len(book_data.get("chapters", [1])))),
                               f"Chapter {idx + 1} ready",
                               {"chapter": chapter, "index": idx})

            ProjectModel.update(project_id, {
                "chapters": chapters,
                "cover_title": book_data.get("title", project.get("title")),
                "cover_subtitle": book_data.get("subtitle", ""),
                "status": "chapters_ready",
            })

            _emit_progress(project_id, "chapters_complete", 100, "All chapters ready", {
                "chapters": chapters,
                "cover_title": book_data.get("title"),
                "cover_subtitle": book_data.get("subtitle", ""),
            })

            if auto_images:
                # Trigger batch image generation in another thread
                socketio.start_background_task(lambda: _do_generate_all_images(app, project_id))

    except Exception as e:
        logger.error(f"Internal book gen error: {e}")
        _emit_progress(project_id, "error", 0, f"Auto-generation failed: {str(e)}")


def _do_generate_all_images(app, project_id):
    """Internal task for batch image generation."""
    try:
        with app.app_context():
            project = ProjectModel.find_by_id(project_id)
            if not project: return
            
            chapters = project.get("chapters", [])
            service = _get_image_generator(app)
            max_workers = 3 # Slightly lower for auto-flow to prevent overload
            
            def _process_single_chapter(chapter_data):
                idx, chapter = chapter_data
                try:
                    # Add jitter to prevent API rate-limiting during parallel bursts
                    time.sleep(random.uniform(0.5, 2.5))
                    
                    summary = chapter.get("chapter_summary", chapter.get("chapter_title", ""))
                    
                    result = guardian.safe_execute(
                        "image_generation",
                        primary_func=lambda: service.generate_chapter_image(summary),
                        default_value={"url": None} # download_image handles None by using placeholder
                    )
                    
                    if result.get("url"):
                        upload_dir = os.path.join(app.config["UPLOAD_FOLDER"], "images")
                        filename = f"ai_{uuid.uuid4()}.jpg"
                        filepath = os.path.join(upload_dir, filename)
                        service.download_image(result["url"], filepath)
                        image_url = f"/api/unguided/images/{filename}"
                    else:
                        # Force placeholder if No URL
                        filename = f"ai_{uuid.uuid4()}.jpg"
                        filepath = os.path.join(app.config["UPLOAD_FOLDER"], "images", filename)
                        service._generate_local_placeholder("Legacy", filepath)
                        image_url = f"/api/unguided/images/{filename}"

                    ProjectModel.update_chapter(project_id, chapter["id"], {
                        "image_url": image_url,
                        "image_type": "ai",
                    })
                    
                    _emit_progress(project_id, "image_ready", 
                                   int(((idx + 1) / len(chapters)) * 100),
                                   f"Illustration {idx + 1}/{len(chapters)} ready",
                                   {"chapter_id": chapter["id"], "image_url": image_url})
                except Exception as e:
                    logger.error(f"Auto-image failed for chapter {idx}: {e}")

            _emit_progress(project_id, "generating_images", 0, "Illustrating your legacy...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                list(executor.map(_process_single_chapter, enumerate(chapters)))

            ProjectModel.update(project_id, {"status": "images_ready"})
            _emit_progress(project_id, "all_images_complete", 100, "Legacy masterfully illustrated")

    except Exception as e:
        logger.error(f"Auto batch images error: {e}")


@unguided_bp.route("/generate-book", methods=["POST"])
@jwt_required()
def generate_book():
    """Generate full book from transcript."""
    user_id = get_jwt_identity()
    data = request.get_json()

    project_id = data.get("project_id")
    if not project_id:
        return jsonify({"error": "project_id is required"}), 400

    project = ProjectModel.find_by_id(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    transcript = project.get("refined_text") or project.get("transcript", "")
    if not transcript:
        return jsonify({"error": "No transcript to generate from"}), 400

    app = current_app._get_current_object()

    def _generate():
        try:
            with app.app_context():
                _emit_progress(project_id, "writing", 10, "Writing your story...")

                def _retry_cb(attempt, wait):
                    if attempt == 88:
                        msg = "Cloud is busy, switching to secondary processor..."
                    elif attempt == 77:
                        msg = "Cloud services exhausted — engaging Private AI (Offline)..."
                    else:
                        msg = f"AI is busy, retrying in {wait}s (attempt {attempt})..."
                    _emit_progress(project_id, "writing", 10, msg)

                writer = _get_story_writer(app)
                book_data = writer.generate_book(
                    transcript,
                    title=project.get("title", "My Story"),
                    retry_callback=_retry_cb
                )

                _emit_progress(project_id, "writing", 70, "Book structure complete")

                # Build chapter list
                chapters = []
                for idx, ch in enumerate(book_data.get("chapters", [])):
                    chapter = {
                        "id": str(uuid.uuid4()),
                        "chapter_title": ch.get("chapter_title", f"Chapter {idx + 1}"),
                        "chapter_summary": ch.get("chapter_summary", ""),
                        "content": ch.get("content", ""),
                        "image_url": None,
                        "image_type": None,
                        "locked": False,
                    }
                    chapters.append(chapter)

                    # Stream each chapter as it's ready
                    _emit_progress(project_id, "chapter_ready", int(70 + (25 * (idx + 1) / len(book_data.get("chapters", [1])))),
                                   f"Chapter {idx + 1} ready",
                                   {"chapter": chapter, "index": idx})

                ProjectModel.update(project_id, {
                    "chapters": chapters,
                    "cover_title": book_data.get("title", project.get("title")),
                    "cover_subtitle": book_data.get("subtitle", ""),
                    "status": "chapters_ready",
                })

                _emit_progress(project_id, "chapters_complete", 100, "All chapters ready", {
                    "chapters": chapters,
                    "cover_title": book_data.get("title"),
                    "cover_subtitle": book_data.get("subtitle", ""),
                })

        except Exception as e:
            logger.error(f"Book generation error: {e}")
            _emit_progress(project_id, "error", 0, f"Book generation failed: {str(e)}")

    socketio.start_background_task(_generate)
    return jsonify({"message": "Book generation started"}), 202


# ============================================================
# IMAGE GENERATION
# ============================================================

@unguided_bp.route("/generate-image", methods=["POST"])
@jwt_required()
def generate_image():
    """Generate AI image for a chapter."""
    user_id = get_jwt_identity()
    data = request.get_json()

    project_id = data.get("project_id")
    chapter_id = data.get("chapter_id")
    chapter_summary = data.get("chapter_summary", "")

    if not project_id or not chapter_id:
        return jsonify({"error": "project_id and chapter_id are required"}), 400

    app = current_app._get_current_object()

    def _generate():
        try:
            with app.app_context():
                _emit_progress(project_id, "generating_image", 20,
                               f"Generating image...")

                service = _get_image_generator(app)
                with HeartbeatSender(project_id, "generating_image", 40, "Our AI artists are working on your illustration..."):
                    result = guardian.safe_execute(
                        "standalone_image_gen",
                        primary_func=lambda: service.generate_chapter_image(chapter_summary),
                        default_value={"url": None}
                    )

                _emit_progress(project_id, "generating_image", 50,
                               "Downloading image...")

                # Always download locally for reliability
                upload_dir = os.path.join(app.config["UPLOAD_FOLDER"], "images")
                filename = f"ai_{uuid.uuid4()}.jpg"
                filepath = os.path.join(upload_dir, filename)
                
                if result.get("url"):
                    service.download_image(result["url"], filepath)
                else:
                    service._generate_local_placeholder("Memoir", filepath)
                
                image_url = f"/api/unguided/images/{filename}"
                logger.info(f"Image cached locally: {image_url}")

                # Try Cloudinary upload if configured
                try:
                    cloud_name = app.config.get("CLOUDINARY_CLOUD_NAME")
                    if cloud_name and cloud_name != "VANSH":
                        cloudinary_service = CloudinaryService(
                            cloud_name,
                            app.config.get("CLOUDINARY_API_KEY"),
                            app.config.get("CLOUDINARY_API_SECRET")
                        )
                        cloud_result = cloudinary_service.upload_image(filepath)
                        image_url = cloud_result["url"]
                        logger.info(f"Image uploaded to Cloudinary: {image_url}")
                except Exception as cloud_err:
                    logger.warning(f"Cloudinary upload failed, using local: {cloud_err}")

                # Update chapter with URL
                ProjectModel.update_chapter(project_id, chapter_id, {
                    "image_url": image_url,
                    "image_type": "ai",
                })

                _emit_progress(project_id, "image_ready", 100,
                               "Image generated and saved",
                               {"chapter_id": chapter_id, "image_url": image_url})

        except Exception as e:
            logger.error(f"Image generation error: {e}")
            _emit_progress(project_id, "error", 0, f"Image generation failed: {str(e)}")

    thread = threading.Thread(target=_generate)
    thread.start()

    return jsonify({"message": "Image generation started"}), 202


@unguided_bp.route("/generate-all-images", methods=["POST"])
@jwt_required()
def generate_all_images():
    """Generate AI images for all chapters."""
    user_id = get_jwt_identity()
    data = request.get_json()

    project_id = data.get("project_id")
    if not project_id:
        return jsonify({"error": "project_id is required"}), 400

    project = ProjectModel.find_by_id(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    app = current_app._get_current_object()

    def _generate_all():
        try:
            with app.app_context():
                chapters = project.get("chapters", [])
                service = _get_image_generator(app)
                
                # We use a ThreadPoolExecutor to generate images in parallel
                # MAX_WORKERS set to 5 to balance speed vs server load
                max_workers = 5
                
                def _process_single_chapter(chapter_data):
                    idx, chapter = chapter_data
                    existing_url = chapter.get("image_url")
                    if existing_url:
                        # Skip only if it's a valid local or Cloudinary URL
                        # Re-generate if it's a broken Pollinations URL
                        if not existing_url.startswith("https://image.pollinations.ai"):
                            return None
                        
                    try:
                        summary = chapter.get("chapter_summary", chapter.get("chapter_title", ""))
                        result = service.generate_chapter_image(summary)
                        
                        # Always download locally first
                        upload_dir = os.path.join(app.config["UPLOAD_FOLDER"], "images")
                        filename = f"ai_{uuid.uuid4()}.jpg"
                        filepath = os.path.join(upload_dir, filename)
                        service.download_image(result["url"], filepath)
                        image_url = f"/api/unguided/images/{filename}"

                        # Try Cloudinary if configured
                        try:
                            cloud_name = app.config.get("CLOUDINARY_CLOUD_NAME")
                            if cloud_name and cloud_name != "VANSH":
                                cloudinary_service = CloudinaryService(
                                    cloud_name,
                                    app.config.get("CLOUDINARY_API_KEY"),
                                    app.config.get("CLOUDINARY_API_SECRET")
                                )
                                cloud_result = cloudinary_service.upload_image(filepath)
                                image_url = cloud_result["url"]
                        except Exception as cloud_err:
                            logger.warning(f"Cloudinary batch upload failed for chapter {idx}: {cloud_err}")

                        # Update DB
                        ProjectModel.update_chapter(project_id, chapter["id"], {
                            "image_url": image_url,
                            "image_type": "ai",
                        })
                        
                        # Emit update for THIS chapter
                        _emit_progress(project_id, "image_ready", 
                                       int(((idx + 1) / len(chapters)) * 100),
                                       f"Image {idx + 1}/{len(chapters)} ready",
                                       {"chapter_id": chapter["id"], "image_url": image_url})
                        
                        return True
                    except Exception as e:
                        logger.error(f"Failed to generate image for chapter {idx}: {e}")
                        return False

                # Map chapters to indexed list for tracking
                chapter_list = list(enumerate(chapters))
                
                _emit_progress(project_id, "generating_images", 0, f"Starting parallel generation of {len(chapters)} images...")
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Start the load operations and mark each future with its index
                    future_to_chapter = {executor.submit(_process_single_chapter, c): c for c in chapter_list}
                    for future in concurrent.futures.as_completed(future_to_chapter):
                        # Result handled inside _process_single_chapter (emits socket updates)
                        pass

                ProjectModel.update(project_id, {"status": "images_ready"})
                _emit_progress(project_id, "all_images_complete", 100, "All images generated successfully")

        except Exception as e:
            logger.error(f"Batch image generation error: {e}")
            _emit_progress(project_id, "error", 0, f"Batch image generation failed: {str(e)}")

    socketio.start_background_task(_generate_all)
    return jsonify({"message": "Batch image generation started"}), 202


@unguided_bp.route("/download-docx/<project_id>", methods=["GET"])
@jwt_required_with_query()
def download_docx(project_id):
    """Generate and send Word document."""
    try:
        project = ProjectModel.find_by_id(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        output_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "docx")
        service = DocxGeneratorService(output_dir)
        
        filename = f"{project.get('title', 'My Story').replace(' ', '_')}.docx"
        filepath = service.generate(project, filename=filename)

        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        logger.error(f"DOCX download error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# MANUAL IMAGE UPLOAD
# ============================================================

@unguided_bp.route("/upload-image", methods=["POST"])
@jwt_required()
def upload_image():
    """Upload a manual image for a chapter."""
    user_id = get_jwt_identity()

    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]
    project_id = request.form.get("project_id")
    chapter_id = request.form.get("chapter_id")

    if not project_id or not chapter_id:
        return jsonify({"error": "project_id and chapter_id are required"}), 400

    if not _allowed_file(file.filename, current_app.config["ALLOWED_IMAGE_EXTENSIONS"]):
        return jsonify({"error": "Unsupported image format"}), 400

    # Save image (no longer needed for long term, but good for buffer)
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "images")
    os.makedirs(upload_dir, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    # Determine if we should use Cloudinary or Local
    image_url = f"/api/unguided/images/{filename}"
    use_local = True

    try:
        cloud_name = current_app.config.get("CLOUDINARY_CLOUD_NAME")
        if cloud_name and cloud_name != "VANSH":
            cloudinary_service = CloudinaryService(
                cloud_name,
                current_app.config.get("CLOUDINARY_API_KEY"),
                current_app.config.get("CLOUDINARY_API_SECRET")
            )
            cloud_result = cloudinary_service.upload_image(filepath)
            image_url = cloud_result["url"]
            use_local = False
            logger.info(f"Manual image uploaded to Cloudinary: {image_url}")
        else:
            logger.info("Cloudinary invalid, using local serving for manual image.")
    except Exception as e:
        logger.warning(f"Manual Cloudinary upload failed: {e}. Falling back to local.")

    ProjectModel.update_chapter(project_id, chapter_id, {
        "image_url": image_url,
        "image_type": "manual",
    })

    # Clean up local file ONLY if it was successfully uploaded to Cloudinary
    if not use_local:
        try:
            os.remove(filepath)
        except OSError:
            pass

    return jsonify({
        "message": "Image saved successfully",
        "image_url": image_url,
        "storage": "cloudinary" if not use_local else "local"
    }), 200


@unguided_bp.route("/images/<filename>", methods=["GET"])
def serve_image(filename):
    """Serve uploaded images."""
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "images")
    filepath = os.path.join(upload_dir, secure_filename(filename))

    if not os.path.exists(filepath):
        return jsonify({"error": "Image not found"}), 404

    return send_file(filepath)


# ============================================================
# PDF GENERATION
# ============================================================

@unguided_bp.route("/generate-pdf", methods=["POST"])
@jwt_required()
def generate_pdf():
    """Generate final PDF book."""
    user_id = get_jwt_identity()
    data = request.get_json()

    project_id = data.get("project_id")
    if not project_id:
        return jsonify({"error": "project_id is required"}), 400

    project = ProjectModel.find_by_id(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    app = current_app._get_current_object()

    def _generate():
        try:
            with app.app_context():
                _emit_progress(project_id, "generating_pdf", 20, "Generating PDF...")

                service = PDFGeneratorService(
                    os.path.join(app.config["UPLOAD_FOLDER"], "pdfs")
                )
                with HeartbeatSender(project_id, "generating_pdf", 50, "Finalizing your legacy into a beautiful PDF..."):
                    pdf_path = service.generate(project, filename=f"{project_id}.pdf")

                pdf_url = f"/api/unguided/pdf/{project_id}.pdf"
                ProjectModel.update(project_id, {
                    "pdf_url": pdf_url,
                    "status": "complete",
                })

                _emit_progress(project_id, "pdf_ready", 100, "PDF ready", {
                    "pdf_url": pdf_url,
                })

        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            _emit_progress(project_id, "error", 0, f"PDF generation failed: {str(e)}")

    socketio.start_background_task(_generate)
    return jsonify({"message": "PDF generation started"}), 202


@unguided_bp.route("/pdf/<filename>", methods=["GET"])
@jwt_required_with_query()
def download_pdf(filename):
    """Download generated PDF."""
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "pdfs")
    filepath = os.path.join(upload_dir, secure_filename(filename))

    if not os.path.exists(filepath):
        return jsonify({"error": "PDF not found"}), 404

    return send_file(filepath, as_attachment=True, download_name=filename)
