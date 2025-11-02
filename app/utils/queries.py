import sqlite3
import pandas as pd
import os 


def get_playlists_query() -> str:
    return "SELECT id, name FROM playlists ORDER BY name"

GET_PLAYLISTS_QUERY: str="SELECT id, name FROM playlists ORDER BY name"

def get_songs_from_playlist_query(playlist_id) -> str:

    return """
        SELECT 
            s.song_id, 
            s.title,
            s.artists,
            s.mp4_path, 
            s.copertina_640_path AS cover_path
        FROM 
            songs s 
        JOIN 
            playlist_songs ps 
        ON 
            s.song_id = ps.song_id
        WHERE 
            ps.playlist_id = {playlist_id}
    """.format(playlist_id=playlist_id)


GET_SONGS_FROM_PLAYLIST_QUERY = """
        SELECT 
            s.song_id, 
            s.title,
            s.artists,
            s.mp4_path, 
            s.copertina_640_path AS cover_path
        FROM 
            songs s 
        JOIN 
            playlist_songs ps 
        ON 
            s.song_id = ps.song_id
        WHERE 
            ps.playlist_id = ?
    """

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'db', 'music-player.db')
db_conn = sqlite3.connect(DATABASE_PATH)

def test_query(query: str, db_conn=db_conn):
    try:
        cursor = db_conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()

        # Estrai i nomi delle colonne dal cursore
        columns = [desc[0] for desc in cursor.description]

        # Crea il DataFrame con nomi di colonna
        df = pd.DataFrame(result, columns=columns)

        # Stampa informazioni utili
        print(df.info())     # <-- nota le parentesi
        print(df.head(3))
        print(df.columns)

    except Exception as e:
        print(f"Error calling db: {e}")

# tests
if __name__=='__main__':

    import sys

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print(PROJECT_ROOT)
    print(DATABASE_PATH)

    # test_query(GET_PLAYLISTS_QUERY)
    test_query(get_songs_from_playlist_query(21))
