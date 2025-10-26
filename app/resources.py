import os 

# defining the base directory - di dir access to the current file
APP_DIR = os.path.dirname(os.path.abspath(__file__))

PJ_DIR = os.path.join(APP_DIR, 'new_music-palyer')

# now the new_music-palyer directory is in Desktop where is it also present: mp4 dir and copertine dir

# desktop pc access path
DESKTOP_DIR = os.path.join(os.path.expanduser('~'), 'Desktop')

# desktop pc mp4 and copertine dir access path
MP4_DIR = os.path.join(DESKTOP_DIR, 'mp4')
COPERTINE_DIR = os.path.join(DESKTOP_DIR, 'copertine')