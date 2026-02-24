"""
Library Initializer — Ensures all local models/data are downloaded.
"""

import nltk
import spacy
import logging
import os

logger = logging.getLogger(__name__)

_NLTK_PACKAGES = [
    ('tokenizers/punkt', 'punkt'),
    ('tokenizers/punkt_tab', 'punkt_tab'),
    ('taggers/averaged_perceptron_tagger', 'averaged_perceptron_tagger'),
    ('corpora/wordnet', 'wordnet'),
    ('corpora/omw-1.4', 'omw-1.4'),
]


def _ensure_nltk(resource_path, package_name):
    """Download NLTK package only if not already present."""
    try:
        nltk.data.find(resource_path)
    except LookupError:
        logger.info(f"Downloading NLTK package: {package_name}")
        nltk.download(package_name, quiet=True)


def init_all():
    """Download necessary local data for NLP and ML libraries."""
    logger.info("Initializing library core...")
    
    # 1. NLTK Data — skip downloads if already present
    try:
        for resource_path, package_name in _NLTK_PACKAGES:
            _ensure_nltk(resource_path, package_name)
        logger.info("NLTK data ready.")
    except Exception as e:
        logger.warning(f"NLTK initialization error: {e}")

    # 2. Spacy Models — skip if already installed
    try:
        if not spacy.util.is_package("en_core_web_sm"):
            logger.info("Downloading en_core_web_sm model...")
            spacy.cli.download("en_core_web_sm")
        logger.info("Spacy models ready.")
    except Exception as e:
        logger.warning(f"Spacy initialization error: {e}")

    # 3. Create necessary local directories
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    folders = [
        "uploads/raw",
        "uploads/processed",
        "uploads/pdfs",
        "uploads/docx",
        "uploads/images"
    ]
    for folder in folders:
        path = os.path.join(base_dir, folder)
        os.makedirs(path, exist_ok=True)

    # 4. Pre-warm heavy models in background to avoid first-request lag
    import threading
    def _warmup_background():
        try:
            logger.info("Pre-warming heavy AI models in background...")
            # 4a. Warm up Faster-Whisper
            from app.services.local_transcription import LocalTranscriptionService
            ts = LocalTranscriptionService()
            ts._load_model()
            logger.info("Faster-Whisper pre-warmed.")

            # 4b. Warm up Local NLP (Transformers)
            from app.services.local_nlp import LocalNLPService
            nlp = LocalNLPService()
            nlp._load_model()
            logger.info("Local NLP pre-warmed.")
            
            logger.info("All heavy models pre-warmed successfully.")
        except Exception as e:
            logger.warning(f"Background pre-warm error: {e}")

    threading.Thread(target=_warmup_background, daemon=True).start()

    logger.info("Library core initialization complete.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_all()

