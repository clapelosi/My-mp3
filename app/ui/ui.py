import os
import threading
import sqlite3
from tkinter import (
    Label, 
    Button, 
    Frame, 
    StringVar, 
    PhotoImage, 
    Listbox, 
    Scrollbar
)
from tkinter import ttk
from PIL import Image, ImageTk

from app import settings
from app import utils
from app.music_player.music_palyer import MusicPlayer

from app.utils.queries import (
    get_playlists_query, 
    get_songs_from_playlist_query,
    GET_PLAYLISTS_QUERY, 
    GET_SONGS_FROM_PLAYLIST_QUERY
)


class App:
    """
    Classe principale dell'applicazione che gestisce l'interfaccia utente (UI)
    per il lettore musicale.
    """
    def __init__(self, root):
        """
        Inizializza l'applicazione.

        Args:
            root: La finestra principale di Tkinter.
        """
        self.root = root
        self.root.title(settings.WINDOW_TITLE)
        self.root.configure(bg=settings.BACKGROUND_COLOR)

        # Connessione al database SQLite
        self.db_conn = sqlite3.connect(settings.DATABASE_PATH)
        self.playlists = []  # Lista per memorizzare le playlist come tuple (id, name)

        # Istanza del lettore musicale
        self.player = MusicPlayer(self.update_ui_for_song)

        # Impostazione degli stili e creazione dei widget
        self.setup_styles()
        self.create_widgets() # at line 59
        self.load_playlists_from_db() # at line 193

        # Thread per monitorare la fine delle tracce musicali in background
        self.playback_thread = threading.Thread(target=self.player.run_playlist_monitor, daemon=True)
        self.playback_thread.start()

        # Avvia l'aggiornamento periodico della barra di progresso
        self.update_progress() 
        # Gestisce la chiusura della finestra
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # === UI Setup ===
    def setup_styles(self):
        """Configura gli stili personalizzati per i widget ttk."""
        style = ttk.Style()
        style.theme_use('clam')
        # Stile per la barra di progresso
        style.configure("dark.Horizontal.TProgressbar",
                        troughcolor=settings.COMPONENT_BACKGROUND,
                        background=settings.PRIMARY_COLOR,
                        bordercolor=settings.BACKGROUND_COLOR)
        # Stile per lo slider del volume
        style.configure("dark.Horizontal.TScale",
                        troughcolor=settings.COMPONENT_BACKGROUND,
                        background=settings.PRIMARY_COLOR,
                        bordercolor=settings.BACKGROUND_COLOR)
        # Stili globali per Label e Frame
        style.configure("TLabel", background=settings.BACKGROUND_COLOR, foreground=settings.TEXT_COLOR)
        style.configure("TFrame", background=settings.BACKGROUND_COLOR)

    def create_widgets(self):
        """Crea e posiziona tutti i widget nell'interfaccia utente."""
        # Frame principale che contiene tutto
        main_frame = Frame(self.root, bg=settings.BACKGROUND_COLOR)
        main_frame.pack(padx=10, pady=10, fill='both', expand=True)

        # === COLONNA SINISTRA ===
        left_frame = Frame(main_frame, bg=settings.BACKGROUND_COLOR)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Frame per la copertina dell'album
        cover_frame = Frame(left_frame, bg=settings.BACKGROUND_COLOR)
        cover_frame.pack(pady=10, fill='both', expand=True)

        self.cover_label = Label(cover_frame, bg=settings.BACKGROUND_COLOR)
        self.cover_label.pack(fill='both', expand=True)

        # Frame per le informazioni della canzone (titolo, tempo, progress bar)
        # Frame per le informazioni della canzone (titolo-artisti, tempo, progress bar)
        info_frame = Frame(left_frame, bg=settings.BACKGROUND_COLOR)
        info_frame.pack(pady=5, fill='x')
        self.song_title_var = StringVar(value="Nessuna canzone in riproduzione")
        Label(info_frame, textvariable=self.song_title_var,
              fg=settings.TEXT_COLOR, bg=settings.BACKGROUND_COLOR,
              font=(settings.FONT_FAMILY, settings.FONT_SIZE_TITLE)).pack()
        self.time_var = StringVar(value="--:-- / --:--")
        Label(info_frame, textvariable=self.time_var,
              fg=settings.MUTED_TEXT_COLOR, bg=settings.BACKGROUND_COLOR,
              font=(settings.FONT_FAMILY, settings.FONT_SIZE_TIME)).pack()
        self.progress_bar = ttk.Progressbar(info_frame, orient='horizontal',
                                            mode='determinate', style="dark.Horizontal.TProgressbar")
        self.progress_bar.pack(pady=5, fill='x', expand=True)

        # Frame per i controlli di riproduzione (play, pausa, etc.)
        controls_frame = Frame(left_frame, bg=settings.BACKGROUND_COLOR)
        controls_frame.pack(pady=10)
        button_font = (settings.FONT_FAMILY, settings.FONT_SIZE_BUTTON, "bold")
        button_config = {
            'bg': settings.COMPONENT_BACKGROUND,
            'fg': settings.TEXT_COLOR,
            'activebackground': settings.ACTIVE_COMPONENT_BACKGROUND,
            'activeforeground': settings.TEXT_COLOR,
            'border': 0,
            **settings.CONTROL_BUTTON_SIZE
        }
        # Creazione dei bottoni
        Button(controls_frame, text="⏮", font=button_font, command=self.player.prev_track, **button_config).grid(row=0, column=0, padx=5)
        self.play_pause_button = Button(controls_frame, text="▶", font=button_font,
                                        command=self.toggle_play_pause, **button_config)
        self.play_pause_button.grid(row=0, column=1, padx=5)
        Button(controls_frame, text="⏭", font=button_font, command=self.player.next_track, **button_config).grid(row=0, column=2, padx=5)
        Button(controls_frame, text="⏹", font=button_font, command=self.player.stop, **button_config).grid(row=0, column=3, padx=5)
        Button(controls_frame, text="🔀", font=button_font, command=self.toggle_shuffle_ui, **button_config).grid(row=0, column=4, padx=5)

        # Frame per il controllo del volume
        volume_frame = Frame(left_frame, bg=settings.BACKGROUND_COLOR)
        volume_frame.pack(pady=5, fill='x')
        Label(volume_frame, text="🔉", bg=settings.BACKGROUND_COLOR,
              fg=settings.TEXT_COLOR, font=(settings.FONT_FAMILY, 12)).pack(side='left')
        self.volume_slider = ttk.Scale(volume_frame, from_=0, to=100, orient='horizontal',
                                       command=self.player.set_volume, style="dark.Horizontal.TScale")
        self.volume_slider.set(100)  # Imposta il volume iniziale al 100%
        self.volume_slider.pack(side='left', fill='x', expand=True, padx=5)
        Label(volume_frame, text="🔊", bg=settings.BACKGROUND_COLOR,
              fg=settings.TEXT_COLOR, font=(settings.FONT_FAMILY, 12)).pack(side='left')

        # === COLONNA DESTRA ===
        right_frame = Frame(main_frame, bg=settings.BACKGROUND_COLOR, width=250)
        right_frame.pack(side='right', fill='y', expand=False, padx=(10, 0))
        right_frame.pack_propagate(False)  # Impedisce al frame di ridimensionarsi

        # Finestra "paned" per dividere lo spazio tra playlist e canzoni
        paned_window = ttk.PanedWindow(right_frame, orient='vertical')
        paned_window.pack(fill='both', expand=True)

        # Frame per la lista delle playlist
        playlist_frame = Frame(paned_window, bg=settings.BACKGROUND_COLOR)
        Label(playlist_frame, text="My Playlists",
              font=(settings.FONT_FAMILY, 14), fg=settings.TEXT_COLOR,
              bg=settings.BACKGROUND_COLOR).pack(pady=(0, 5))

        playlist_container = Frame(playlist_frame)
        playlist_container.pack(fill='both', expand=True)

        self.playlist_box = Listbox(playlist_container, bg=settings.COMPONENT_BACKGROUND, fg=settings.TEXT_COLOR,
                                    selectbackground=settings.PRIMARY_COLOR, highlightthickness=0, border=0,
                                    font=(settings.FONT_FAMILY, settings.FONT_SIZE_PLAYLIST), exportselection=False)
        self.playlist_box.pack(side='left', fill='both', expand=True)
        self.playlist_box.bind("<Double-1>", self.load_songs_for_playlist)

        scrollbar_playlist = Scrollbar(playlist_container, orient='vertical', command=self.playlist_box.yview)
        scrollbar_playlist.pack(side='right', fill='y')
        self.playlist_box.config(yscrollcommand=scrollbar_playlist.set)

        paned_window.add(playlist_frame, weight=1)

        # Frame per la lista delle canzoni
        songs_frame = Frame(paned_window, bg=settings.BACKGROUND_COLOR)
        Label(songs_frame, text="Canzoni 🎵", font=(settings.FONT_FAMILY, 14),
              fg=settings.TEXT_COLOR, bg=settings.BACKGROUND_COLOR).pack(pady=(0, 5))

        songs_container = Frame(songs_frame)
        songs_container.pack(fill='both', expand=True)

        self.song_box = Listbox(songs_container, bg=settings.COMPONENT_BACKGROUND, fg=settings.TEXT_COLOR,
                                selectbackground=settings.PRIMARY_COLOR, highlightthickness=0, border=0,
                                font=(settings.FONT_FAMILY, settings.FONT_SIZE_PLAYLIST), exportselection=False)
        self.song_box.pack(side='left', fill='both', expand=True)
        self.song_box.bind("<Double-1>", self.play_selected_song)

        scrollbar_songs = Scrollbar(songs_container, orient='vertical', command=self.song_box.yview)
        scrollbar_songs.pack(side='right', fill='y')
        self.song_box.config(yscrollcommand=scrollbar_songs.set)

        paned_window.add(songs_frame, weight=2)

    # === Metodi funzionali ===
    def load_playlists_from_db(self):
        """Carica i nomi delle playlist dal database e li visualizza nella Listbox."""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT id, name FROM playlists ORDER BY name")
            # cursor.execute(get_playlists_query())
            # cursor.execute(GET_PLAYLISTS_QUERY)
            self.playlists = cursor.fetchall()

            self.playlist_box.delete(0, 'end')  # Pulisce la lista prima di caricarla
            for _, name in self.playlists:
                self.playlist_box.insert('end', name)
        except Exception as e:
            print(f"Errore nel caricamento delle playlist: {e}")

    def load_songs_for_playlist(self, event=None):
        """Carica le canzoni associate alla playlist selezionata."""
        selected_indices = self.playlist_box.curselection()
        if not selected_indices:
            return

        playlist_index = selected_indices[0]
        playlist_id, playlist_name = self.playlists[playlist_index]
        print(f"Caricamento canzoni per playlist: {playlist_name} (ID: {playlist_id})")

        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT 
                    s.song_id, -- index 0
                    s.title, -- index 1
                    s.mp4_path, -- index 2
                    s.copertina_640_path AS cover_path -- index 3,
                    s.artists  -- index 4
                FROM songs s
                JOIN playlist_songs ps ON s.song_id = ps.song_id
                WHERE ps.playlist_id = ?
            """, (playlist_id,))
            # cursor.execute(get_songs_from_playlist_query(playlist_id))
            # cursor.execute(GET_SONGS_FROM_PLAYLIST_QUERY, (playlist_id,))
            self.current_song_list = cursor.fetchall()

            self.song_box.delete(0, 'end')  # Pulisce la lista delle canzoni
            for _, title, _, _ in self.current_song_list:
                self.song_box.insert('end', title)

        except Exception as e:
            print(f"Errore nel caricare le canzoni della playlist: {e}")

    def play_selected_song(self, event=None):
        """Avvia la riproduzione della canzone selezionata dalla lista."""
        selected_indices = self.song_box.curselection()
        if not selected_indices:
            return
        
        song_index = selected_indices[0]
        # Prepara la lista di canzoni per il player
        songs_for_player = [(s[2], s[1], s[3], s[4]) for s in self.current_song_list]
        self.player.load_playlist(songs_for_player)
        self.player.play_song_at_index(song_index)

    def update_ui_for_song(self, file_path, song_title, index):
        """Aggiorna l'interfaccia utente (titolo, copertina, selezione) per la canzone corrente."""
        self.song_title_var.set(song_title)

        cover_path = None
        if hasattr(self, 'current_song_list') and 0 <= index < len(self.current_song_list):
            cover_path = self.current_song_list[index][3]

        if cover_path and os.path.exists(cover_path):
            try:
                img = Image.open(cover_path)
                # Ridimensiona l'immagine per adattarla alla label
                label_w = self.cover_label.winfo_width() or 640
                label_h = self.cover_label.winfo_height() or 640
                img.thumbnail((label_w, label_h))
                cover_img = ImageTk.PhotoImage(img)
                self.cover_label.configure(image=cover_img)
                self.cover_label.image = cover_img  # Mantiene un riferimento all'immagine
            except Exception as e:
                print(f"Errore caricamento copertina: {e}")
        else:
            # Mostra un placeholder se la copertina non è disponibile
            placeholder = PhotoImage(width=640, height=640)
            self.cover_label.configure(image=placeholder, text="Copertina non trovata",
                                       fg=settings.TEXT_COLOR, compound='center')
            self.cover_label.image = placeholder

        # Aggiorna la selezione nella lista delle canzoni
        self.song_box.selection_clear(0, 'end')
        self.song_box.selection_set(index)
        self.song_box.activate(index)
        self.song_box.see(index)  # Assicura che la canzone selezionata sia visibile

    def toggle_play_pause(self):
        """Gestisce il click sul pulsante play/pausa."""
        self.player.toggle_pause()
        new_text = "▶" if self.player.is_paused else "⏸"
        self.play_pause_button.config(text=new_text)

    def toggle_shuffle_ui(self):
        """Attiva/disattiva la modalità shuffle e aggiorna il colore del bottone."""
        self.player.toggle_shuffle()
        new_color = settings.PRIMARY_COLOR if self.player.shuffle else settings.TEXT_COLOR
        # Trova il bottone shuffle e cambia il colore del testo
        for widget in self.root.winfo_children():
            for subwidget in widget.winfo_children():
                if isinstance(subwidget, Button) and subwidget.cget("text") == "🔀":
                    subwidget.config(fg=new_color)

    def update_progress(self):
        """Aggiorna la barra di progresso e il tempo di riproduzione."""
        if self.player.running:
            current_ms = self.player.player.get_time()
            total_ms = self.player.player.get_length()
            # Aggiorna il testo del tempo
            self.time_var.set(f"{utils.format_time(current_ms)} / {utils.format_time(total_ms)}")
            # Aggiorna la barra di progresso
            if total_ms > 0:
                self.progress_bar['value'] = (current_ms / total_ms) * 100
            else:
                self.progress_bar['value'] = 0
            # Richiama questa funzione dopo 500ms
            self.root.after(500, self.update_progress)

    def on_close(self):
        """Gestisce la chiusura dell'applicazione in modo pulito."""
        self.player.shutdown()  # Ferma la riproduzione e rilascia le risorse
        self.db_conn.close()  # Chiude la connessione al database
        self.root.destroy()  # Distrugge la finestra di Tkinter
