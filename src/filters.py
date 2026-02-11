MUSIC_AI_KEYWORDS = [
    "music", "audio", "sound", "acoustic", "speech",
    "mir", "music information retrieval",
    "music generation", "audio synthesis", "music composition",
    "source separation", "music transcription", "beat tracking",
    "chord recognition", "melody extraction", "singing voice",
    "audio classification", "music recommendation",
    "ismir", "icassp", "dafx",
    "waveform", "spectrogram", "midi", "audio signal",
    "pitch detection", "tempo estimation",
    "music analysis", "audio processing", "sound synthesis",
    "song", "instrument", "musical", "harmony", "rhythm",
    "timbre", "acoustic model", "audio generation",
    "music understanding", "audio feature", "music feature",
    "music tagging", "genre classification", "mood detection",
    "sound event detection", "acoustic scene", "audio event",
    "music similarity", "cover song", "version identification",
    "singing", "vocal", "lyrics", "voice synthesis",
    "audio effect", "music production", "mixing", "mastering",
    "symbolic music", "score", "notation", "music score",
]

def is_music_ai_related(title, summary=""):
    text = (title + " " + summary).lower()
    return any(keyword in text for keyword in MUSIC_AI_KEYWORDS)
