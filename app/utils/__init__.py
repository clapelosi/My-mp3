
import os
from PIL import Image, ImageTk
from app import settings

def load_image(path, size):
    """Carica un'immagine da un percorso, la ridimensiona e la restituisce come PhotoImage."""
    if not path or not os.path.exists(path):
        return None
    try:
        img = Image.open(path)
        img.thumbnail(size)
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Errore durante il caricamento dell'immagine {path}: {e}")
        return None
def format_time(ms):
    """Converte millisecondi in formato MM:SS."""
    if ms is None or ms < 0:
        return "--:--"
    seconds = ms // 1000
    minutes = seconds // 60
    seconds %= 60
    return f"{minutes:02d}:{seconds:02d}"

