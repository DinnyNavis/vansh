# backend/app/utils/model_loader.py

_spacy_model = None
_whisper_model = None


def get_spacy():
    global _spacy_model
    if _spacy_model is None:
        import spacy
        _spacy_model = spacy.load("en_core_web_sm")
    return _spacy_model


def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        _whisper_model = whisper.load_model("base")
    return _whisper_model
