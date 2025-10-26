
import os

# --- Percorsi Fondamentali ---
# Calcola il percorso della root del progetto (la cartella che contiene 'app', 'data', ecc.)
# __file__ -> /path/to/project/app/settings.py
# os.path.dirname(__file__) -> /path/to/project/app
# os.path.dirname(...) -> /path/to/project

# dir of the project on the desktop
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Percorso del database SQLite
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'db/music-player.db')
COVERS_BASE_PATH = os.path.join(os.path.expanduser('~'), 'Desktop', 'copertine')

# --- Impostazioni della UI ---
WINDOW_TITLE = "Music Player DB"
BACKGROUND_COLOR = "#2e2e2e"
PRIMARY_COLOR = "#1e90ff"
TEXT_COLOR = "white"
MUTED_TEXT_COLOR = "lightgrey"
COMPONENT_BACKGROUND = "#404040"
ACTIVE_COMPONENT_BACKGROUND = "#555555"

# --- Dimensioni ---
DEFAULT_COVER_SIZE = (300, 300)
CONTROL_BUTTON_SIZE = {'width': 4, 'height': 2}

# --- Font ---
FONT_FAMILY = "Helvetica"
FONT_SIZE_TITLE = 12
FONT_SIZE_TIME = 9
FONT_SIZE_BUTTON = 14
FONT_SIZE_PLAYLIST = 10
