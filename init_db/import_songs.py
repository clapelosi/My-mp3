
import sqlite3
import json
import os

def create_songs_table(cursor):
    """Crea la tabella 'songs' se non esiste, con la nuova colonna 'cover_path'."""
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS songs (
        song_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        artists TEXT,
        mp4_path TEXT,
        copertina_640_path TEXT,
        copertina_300_path TEXT,
        copertina_64_path TEXT
    )
    """)
    print("Tabella 'songs' creata o già esistente.")

def import_songs_from_json(db_path, songs_json_path):
    """
    Importa le canzoni da un file JSON nel database SQLite.
    Pulisce la tabella prima di importare per evitare dati obsoleti.
    """
    if not os.path.exists(songs_json_path):
        print(f"Errore: Il file '{songs_json_path}' non è stato trovato.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    create_songs_table(cursor)

    # Pulisce la tabella prima di un nuovo import
    print("Pulizia della tabella 'songs' esistente...")
    cursor.execute("DELETE FROM songs")
    conn.commit()

    # Carica i dati delle canzoni dal file JSON
    with open(songs_json_path, 'r', encoding='utf-8') as f:
        songs_data = json.load(f)
    
    print(f"Trovate {len(songs_data)} canzoni da importare da '{songs_json_path}'...")

    songs_to_insert = []
    for song in songs_data:
        # Assicurati che i campi obbligatori esistano
        if 'song_id' in song and 'title' in song:
            songs_to_insert.append((
                song.get('song_id'),
                song.get('title'),
                song.get('artists'),
                song.get('mp4_path'),
                song.get('copertina_640_path'),
                song.get('copertina_300_path'),
                song.get('copertina_64_path'),
            ))

    try:
        cursor.executemany("""
            INSERT INTO songs (song_id, title, artists, mp4_path, copertina_640_path, copertina_300_path, copertina_64_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, songs_to_insert)
        conn.commit()
        print(f"Importate con successo {len(songs_to_insert)} canzoni nel database.")
    except sqlite3.Error as e:
        print(f"Errore durante l'inserimento dei dati nel database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    DATABASE_PATH = 'music-player.db'
    SONGS_JSON_PATH = os.path.join('data', 'data_songs_cleaned.json')
    
    import_songs_from_json(DATABASE_PATH, SONGS_JSON_PATH)
