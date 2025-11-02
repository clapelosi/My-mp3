
import sqlite3
import pandas as pd
import glob
import os
import re

def create_database_tables(cursor):
    """Crea le tabelle 'playlists' e 'playlist_songs' se non esistono."""
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS playlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS playlist_songs (
        playlist_id INTEGER,
        song_id TEXT,
        FOREIGN KEY (playlist_id) REFERENCES playlists(id),
        FOREIGN KEY (song_id) REFERENCES songs(song_id),
        PRIMARY KEY (playlist_id, song_id)
    )
    """)
    print("Tabelle 'playlists' e 'playlist_songs' create o già esistenti.")

def import_playlists_from_csv(db_path, csv_folder_path):
    """
    Importa le playlist dai file CSV nel database SQLite.
    Pulisce le tabelle prima di importare per evitare duplicati.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    create_database_tables(cursor)

    # Opzionale: Pulisce le tabelle prima di un nuovo import
    print("Pulizia delle tabelle delle playlist esistenti...")
    cursor.execute("DELETE FROM playlist_songs")
    cursor.execute("DELETE FROM playlists")
    # Resetta la sequenza di autoincremento per la tabella playlists
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='playlists'")
    conn.commit()


    csv_files = glob.glob(os.path.join(csv_folder_path, '*.csv'))
    print(csv_files)
    print(csv_folder_path)

    if not csv_files:
        print(f"Nessun file CSV trovato in {csv_folder_path}")
        conn.close()
        return

    print(f"Trovati {len(csv_files)} file CSV da importare...")

    for csv_file in csv_files:
        try:
            # Estrai il nome della playlist dal nome del file
            cluster_num = os.path.basename(csv_file).replace('.csv', '')

            # 1. Rimuovo "playlist_1_" iniziale
            cluster_num = re.sub(r'^playlist_\d+_', '', cluster_num)

            # 2. Sostituisco "_" con spazio
            cluster_num = cluster_num.replace('_', ' ')

            # 3. Sostituisco "-" con spazio e capitalizzo ogni parola
            cluster_num = ' '.join(word.capitalize() for word in cluster_num.split('-')).replace('-', ' ')

            # 4. Capitalizzo le parole separate da spazio (tipo canzone -> Canzone)
            playlist_name = ' '.join(word.capitalize() if not re.match(r'\d', word) else word for word in cluster_num.split())

            # Inserisci la nuova playlist nella tabella 'playlists'
            cursor.execute("INSERT INTO playlists (name) VALUES (?)", (playlist_name,))
            playlist_id = cursor.lastrowid
            print(f"Creata playlist '{playlist_name}' con ID: {playlist_id}")

            # Leggi il CSV e inserisci le canzoni nella tabella 'playlist_songs'
            df = pd.read_csv(csv_file)
            songs_to_insert = []
            for song_id in df['song_id']:
                # Verifica se la canzone esiste nella tabella 'songs'
                cursor.execute("SELECT 1 FROM songs WHERE song_id = ?", (song_id,))
                if cursor.fetchone():
                    songs_to_insert.append((playlist_id, song_id))
                else:
                    print(f"Attenzione: song_id '{song_id}' dal file CSV non trovato nella tabella 'songs'. Sarà saltato.")

            cursor.executemany("INSERT INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)", songs_to_insert)
            print(f"  -> Importate {len(songs_to_insert)} canzoni per la playlist '{playlist_name}'.")

        except Exception as e:
            print(f"Errore durante l'elaborazione del file {csv_file}: {e}")
            conn.rollback() # Annulla le modifiche per il file corrente in caso di errore
        else:
            conn.commit() # Conferma le modifiche per il file corrente

    print("\nImportazione completata.")
    conn.close()

if __name__ == '__main__':
    DATABASE_PATH = os.path.join('db','music-player.db')
    CSV_FOLDER = os.path.join('init_db','data', 'csv2')
    import_playlists_from_csv(DATABASE_PATH, CSV_FOLDER)



# ong_id,title,artists,youtube_url,mp4_path,copertina_640_path,copertina_300_path,copertina_64_path