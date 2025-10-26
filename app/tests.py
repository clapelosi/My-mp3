import os
import sys

# Aggiungi la root del progetto (new_music-player) al PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Ora puoi importare da app e dai suoi sottomoduli
from utils import find_cover, format_time


# testing the functions
if __name__ == "__main__":

    print("Testing find_cover function:")
        
    # song_id = "7eJMfftS33KTjuF7lTsMCx"  # example song ID
    song_id = "ab67616d0000b273a3f0e9f20bfbdd1ab8752e39"  # example song ID
    try:
        find_cover(song_id, size=(640, 640))
        print("find_cover executed successfully.")
    except Exception as e:
        print(f"Error during find_cover test: {e}")
