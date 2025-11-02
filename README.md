# Music Player Database

This is a sophisticated desktop music player built in Python, utilizing `tkinter` for the graphical user interface and `vlc` for audio playback. Unlike traditional file-based players, this project uses an SQLite database to manage songs and playlists, allowing for more powerful and structured management of your music library.

## Features

-   **Database-Driven Management:** Your entire music library and playlists are stored in an SQLite database.
-   **Playlist Import:** A dedicated script allows for importing playlists from CSV files.
-   **Intuitive Graphical Interface:** A two-column UI displays playback controls and album art on the left, with available playlists on the right.
-   **Modular Codebase:** The code is structured to separate application logic, settings, and utility functions for better maintainability.

## Project Structure

```
My-mp3/
├── app/                      # Application source code
│   ├── __init__.py
│   ├── main.py               # Main application entry point
│   ├── resources.py          # UI resources (icons, images, etc.)
│   ├── settings.py           # Configuration settings (paths, colors, fonts)
│   ├── tests.py              # Unit tests for the application
│   ├── music_player/         # Core music playback logic
│   │   ├── __init__.py
│   │   └── music_player.py
│   ├── ui/                   # User interface components
│   │   ├── __init__.py
│   │   └── ui.py
│   └── utils/                # Utility functions
│       ├── __init__.py
│       └── queries.py        # Database query functions
├── db/                       # Database related files (e.g., SQLite database file)
├── .gitignore                # Specifies intentionally untracked files to ignore
├── .python-version           # Specifies the Python version to use (e.g., with pyenv)
├── poetry.lock               # Poetry lock file for dependency management
├── pyproject.toml            # Poetry project configuration
├── README.md                 # This documentation file
└── requirements.txt          # Pip requirements file (generated from poetry)
```

## Installation

To get the application running, you will need Python 3, VLC, and the project's Python dependencies. This project uses `poetry` for dependency management.

### 1. System Prerequisites

-   **Python 3:** Ensure you have Python 3 installed on your system.
-   **VLC Media Player:** The application depends on VLC. Install it on your system:
    ```bash
    # On Debian/Ubuntu based systems
    sudo apt-get update
    sudo apt-get install -y vlc
    ```
-   **Tkinter:** The graphical UI library. It's usually included with Python, but on some Linux systems, it needs to be installed separately:
    ```bash
    # On Debian/Ubuntu based systems
    sudo apt-get install -y python3-tk
    ```

### 2. Project Setup

1.  **Clone the repository (if applicable) or download the files.**

2.  **Install Poetry (if you don't have it):**
    ```bash
    pip install poetry
    ```

3.  **Install project dependencies using Poetry:**
    This will create a virtual environment and install all necessary libraries.
    ```bash
    poetry install
    ```

4.  **Activate the Poetry shell:**
    ```bash
    poetry shell
    ```

### 3. Database Population

Before launching the app, you need to import your music data into the database. Run the scripts in the following order: first songs, then playlists.

1.  **Import Songs:**
    Execute the `import_songs.py` script to create and populate the `songs` table with metadata, including paths to your music files and album art.
    ```bash
    python init_db/import_songs.py
    ```

2.  **Import Playlists:**
    Next, run `import_playlists.py` to link the imported songs to their respective playlists.
    ```bash
    python init_db/import_playlists.py
    ```
    -   This script will create the necessary tables and populate the database with playlist data found in the `init_db/data/csv/` folder.

## Launching the Application

Once installation and data import are complete, you can start the music player:

```bash
poetry run python app/main.py
```

A window will open displaying your playlist list on the right. Double-click a playlist to load it and start playback of the first song.