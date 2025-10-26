
# Music Player DB

Questo è un lettore musicale desktop sofisticato costruito in Python con `tkinter` per l'interfaccia grafica e `vlc` per la riproduzione audio. A differenza dei lettori tradizionali basati su file, questo progetto utilizza un database SQLite per gestire le canzoni e le playlist, permettendo una gestione più potente e strutturata della libreria musicale.

## Caratteristiche

- **Gestione a Database:** Tutta la libreria musicale e le playlist sono memorizzate in un database SQLite.
- **Importazione Playlist:** Uno script dedicato permette di importare playlist da file CSV.
- **Interfaccia Grafica Semplice:** Una UI a due colonne mostra i controlli di riproduzione e la copertina a sinistra, e le playlist disponibili a destra.
- **Codice Modulare:** Il codice è stato strutturato per separare la logica dell'applicazione, le impostazioni e le funzioni di utilità.

## Struttura del Progetto

```
new_music-player/
│
├── app/                  # Codice sorgente dell'applicazione
│   ├── __init__.py
│   ├── music_viewer.py   # File principale con la logica della UI
│   ├── settings.py       # File di configurazione (percorsi, colori, font)
│   └── utils/            # Funzioni di utilità
│       └── __init__.py
│
├── data/                 # Dati grezzi e CSV
│   └── csv/              # File CSV contenenti le playlist
│
├── venv/                 # Ambiente virtuale Python (ignorato da git)
│
├── import_playlists.py   # Script per importare i CSV nel database
├── music-player.db       # Database SQLite
├── requirements.txt      # Dipendenze Python del progetto
└── README.md             # Questo file
```

## Installazione

Per far funzionare l'applicazione, è necessario avere Python 3, VLC e alcune librerie Python installate.

### 1. Prerequisiti di Sistema

- **Python 3:** Assicurati di avere Python 3 installato.
- **VLC Media Player:** L'applicazione dipende da VLC. Installalo sul tuo sistema:
  ```bash
  # Su sistemi basati su Debian/Ubuntu
  sudo apt-get update
  sudo apt-get install -y vlc
  ```
- **Tkinter:** La libreria per la UI grafica. Di solito è inclusa con Python, ma su alcuni sistemi Linux va installata a parte:
  ```bash
  # Su sistemi basati su Debian/Ubuntu
  sudo apt-get install -y python3-tk
  ```

### 2. Configurazione del Progetto

1.  **Clona il repository (se fosse su git) o scarica i file.**

2.  **Crea e attiva un ambiente virtuale:**
    Questo isola le dipendenze del progetto.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Installa le dipendenze Python:**
    Usa il file `requirements.txt` per installare tutte le librerie necessarie.
    ```bash
    pip install -r requirements.txt
    ```

### 3. Popolamento del Database

Prima di avviare l'app, devi importare i dati nel database. Esegui gli script in **ordine**: prima le canzoni, poi le playlist.

1.  **Importa le canzoni:**
    Esegui lo script `import_songs.py` per creare e popolare la tabella `songs` con i metadati, inclusi i percorsi dei file musicali e delle copertine.
    ```bash
    ./venv/bin/python import_songs.py
    ```

2.  **Importa le playlist:**
    Successivamente, esegui `import_playlists.py` per collegare le canzoni appena importate alle rispettive playlist.
    ```bash
    ./venv/bin/python import_playlists.py
    ```
- Questo script creerà le tabelle necessarie e popolerà il database con i dati delle playlist trovate nella cartella `data/csv/`.

## Avvio dell'Applicazione

Una volta completata l'installazione e l'importazione dei dati, puoi avviare il lettore musicale:

```bash
./venv/bin/python app/music_viewer.py
```

Si aprirà una finestra dove potrai vedere la lista delle tue playlist sulla destra. Fai doppio clic su una playlist per caricarla e avviare la riproduzione della prima canzone.
