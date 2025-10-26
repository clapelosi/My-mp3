#!/usr/bin/env python3
import os
import sys
import time
import threading
import vlc
import sqlite3
from tkinter import Tk, Label, Button, Frame, StringVar, PhotoImage, Scale, Listbox, Scrollbar
from tkinter import ttk
from PIL import Image, ImageTk
import random

# === Configurazione percorso progetto ===
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importa le impostazioni e le utilità del progetto
from app import settings
from app import utils


# === Classe per la Logica di Riproduzione ===
class MusicPlayer:
    def __init__(self, on_song_change_callback=None):
        self.player = vlc.MediaPlayer()
        self.playlist = []  # Lista di tuple (file_path, titolo, cover_path)
        self.current_index = -1
        self.running = True
        self.is_paused = False
        self.shuffle = False  # ✅ inizializzato
        self.on_song_change = on_song_change_callback

    def load_playlist(self, songs):
        """Carica una nuova playlist di canzoni."""
        self.stop()
        self.playlist = songs
        self.current_index = 0
        self.play_current()

    def play_song_at_index(self, index):
        if 0 <= index < len(self.playlist):
            self.current_index = index
            self.play_current()

    def next_track(self):
        """Passa alla canzone successiva (supporta shuffle)."""
        if not self.playlist:
            return

        if self.shuffle:
            self.current_index = random.randint(0, len(self.playlist) - 1)
        else:
            self.current_index = (self.current_index + 1) % len(self.playlist)

        self.play_current()

    def prev_track(self):
        """Passa alla canzone precedente."""
        if not self.playlist:
            return
        self.current_index = (self.current_index - 1 + len(self.playlist)) % len(self.playlist)
        self.play_current()

    def play_current(self):
        """Riproduce la canzone corrente."""
        if not self.playlist or not (0 <= self.current_index < len(self.playlist)):
            return

        entry = self.playlist[self.current_index]
        if len(entry) == 2:
            file_path, song_title = entry
            cover_path = None
        elif len(entry) >= 3:
            file_path, song_title, cover_path = entry[:3]
        else:
            print("Formato playlist non valido:", entry)
            return

        if not os.path.exists(file_path):
            print(f"Errore: file non trovato -> {file_path}")
            self.next_track()
            return

        media = vlc.Media(file_path)
        self.player.set_media(media)
        self.player.play()
        self.is_paused = False

        if self.on_song_change:
            self.on_song_change(file_path, song_title, self.current_index)

    def toggle_pause(self):
        """Metti in pausa o riprendi la riproduzione."""
        if self.is_paused:
            self.player.play()
            self.is_paused = False
        else:
            self.player.pause()
            self.is_paused = True

    def toggle_shuffle(self):
        """Attiva o disattiva la modalità shuffle."""
        self.shuffle = not self.shuffle
        print(f"Modalità shuffle: {'attiva' if self.shuffle else 'disattivata'}")

    def stop(self):
        self.player.stop()

    def set_volume(self, volume):
        """Imposta il volume (0-100)."""
        self.player.audio_set_volume(int(float(volume)))

    def shutdown(self):
        """Ferma la riproduzione e termina il thread di monitoraggio."""
        self.stop()
        self.running = False

    def run_playlist_monitor(self):
        """Monitora il termine della canzone per passare alla successiva."""
        while self.running:
            time.sleep(1)
            if not self.is_paused and self.player.get_state() == vlc.State.Ended:
                self.next_track()


# === Classe per l'Interfaccia Grafica ===
class App:
    def __init__(self, root):
        self.root = root
        self.root.title(settings.WINDOW_TITLE)
        self.root.configure(bg=settings.BACKGROUND_COLOR)

        self.db_conn = sqlite3.connect(settings.DATABASE_PATH)
        self.playlists = []  # Lista di tuple (id, name)

        self.player = MusicPlayer(self.update_ui_for_song)

        self.setup_styles()
        self.create_widgets()
        self.load_playlists_from_db()

        # Thread per monitorare la fine delle tracce
        self.playback_thread = threading.Thread(target=self.player.run_playlist_monitor, daemon=True)
        self.playback_thread.start()

        # Aggiorna la barra di progresso periodicamente
        self.update_progress()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # === UI Setup ===
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("dark.Horizontal.TProgressbar",
                        troughcolor=settings.COMPONENT_BACKGROUND,
                        background=settings.PRIMARY_COLOR,
                        bordercolor=settings.BACKGROUND_COLOR)
        style.configure("dark.Horizontal.TScale",
                        troughcolor=settings.COMPONENT_BACKGROUND,
                        background=settings.PRIMARY_COLOR,
                        bordercolor=settings.BACKGROUND_COLOR)
        style.configure("TLabel", background=settings.BACKGROUND_COLOR, foreground=settings.TEXT_COLOR)
        style.configure("TFrame", background=settings.BACKGROUND_COLOR)

    def create_widgets(self):
        main_frame = Frame(self.root, bg=settings.BACKGROUND_COLOR)
        main_frame.pack(padx=10, pady=10, fill='both', expand=True)

        # === COLONNA SINISTRA ===
        left_frame = Frame(main_frame, bg=settings.BACKGROUND_COLOR)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Copertina
        cover_frame = Frame(left_frame, bg=settings.BACKGROUND_COLOR)
        cover_frame.pack(pady=10, fill='both', expand=True)

        self.cover_label = Label(cover_frame, bg=settings.BACKGROUND_COLOR)
        self.cover_label.pack(fill='both', expand=True)

        # Info canzone
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

        # Controlli
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
        Button(controls_frame, text="⏮", font=button_font, command=self.player.prev_track, **button_config).grid(row=0, column=0, padx=5)
        self.play_pause_button = Button(controls_frame, text="▶", font=button_font,
                                        command=self.toggle_play_pause, **button_config)
        self.play_pause_button.grid(row=0, column=1, padx=5)
        Button(controls_frame, text="⏭", font=button_font, command=self.player.next_track, **button_config).grid(row=0, column=2, padx=5)
        Button(controls_frame, text="⏹", font=button_font, command=self.player.stop, **button_config).grid(row=0, column=3, padx=5)
        Button(controls_frame, text="🔀", font=button_font, command=self.toggle_shuffle_ui, **button_config).grid(row=0, column=4, padx=5)

        # Volume
        volume_frame = Frame(left_frame, bg=settings.BACKGROUND_COLOR)
        volume_frame.pack(pady=5, fill='x')
        Label(volume_frame, text="🔉", bg=settings.BACKGROUND_COLOR,
              fg=settings.TEXT_COLOR, font=(settings.FONT_FAMILY, 12)).pack(side='left')
        self.volume_slider = ttk.Scale(volume_frame, from_=0, to=100, orient='horizontal',
                                       command=self.player.set_volume, style="dark.Horizontal.TScale")
        self.volume_slider.set(100)
        self.volume_slider.pack(side='left', fill='x', expand=True, padx=5)
        Label(volume_frame, text="🔊", bg=settings.BACKGROUND_COLOR,
              fg=settings.TEXT_COLOR, font=(settings.FONT_FAMILY, 12)).pack(side='left')

        # === COLONNA DESTRA ===
        right_frame = Frame(main_frame, bg=settings.BACKGROUND_COLOR, width=250)
        right_frame.pack(side='right', fill='y', expand=False, padx=(10, 0))
        right_frame.pack_propagate(False)

        paned_window = ttk.PanedWindow(right_frame, orient='vertical')
        paned_window.pack(fill='both', expand=True)

        # Playlist
        playlist_frame = Frame(paned_window, bg=settings.BACKGROUND_COLOR)
        Label(playlist_frame, text="Playlists 📜",
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

        # Canzoni
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
        """Carica i nomi delle playlist dal database."""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT id, name FROM playlists ORDER BY name")
            self.playlists = cursor.fetchall()

            self.playlist_box.delete(0, 'end')
            for _, name in self.playlists:
                self.playlist_box.insert('end', name)
        except Exception as e:
            print(f"Errore nel caricamento delle playlist: {e}")

    def load_songs_for_playlist(self, event=None):
        """Carica le canzoni associate alla playlist selezionata."""
        selected = self.playlist_box.curselection()
        if not selected:
            return

        playlist_id, playlist_name = self.playlists[selected[0]]
        print(f"Caricamento canzoni per playlist: {playlist_name} (ID: {playlist_id})")

        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT s.song_id, s.title, s.mp4_path, s.copertina_640_path AS cover_path
                FROM songs s
                JOIN playlist_songs ps ON s.song_id = ps.song_id
                WHERE ps.playlist_id = ?
            """, (playlist_id,))
            self.current_song_list = cursor.fetchall()

            self.song_box.delete(0, 'end')
            for _, title, _, _ in self.current_song_list:
                self.song_box.insert('end', title)

        except Exception as e:
            print(f"Errore nel caricare le canzoni della playlist: {e}")

    def play_selected_song(self, event=None):
        """Avvia la riproduzione della canzone selezionata."""
        selected = self.song_box.curselection()
        if not selected:
            return
        song_index = selected[0]
        songs_for_player = [(s[2], s[1], s[3]) for s in self.current_song_list]
        self.player.load_playlist(songs_for_player)
        self.player.play_song_at_index(song_index)

    def update_ui_for_song(self, file_path, song_title, index):
        """Aggiorna interfaccia (titolo, copertina, selezione)."""
        self.song_title_var.set(song_title)

        cover_path = None
        if hasattr(self, 'current_song_list') and 0 <= index < len(self.current_song_list):
            cover_path = self.current_song_list[index][3]

        if cover_path and os.path.exists(cover_path):
            try:
                img = Image.open(cover_path)
                label_w = self.cover_label.winfo_width() or 640
                label_h = self.cover_label.winfo_height() or 640
                img.thumbnail((label_w, label_h))
                cover_img = ImageTk.PhotoImage(img)
                self.cover_label.configure(image=cover_img)
                self.cover_label.image = cover_img
            except Exception as e:
                print(f"Errore caricamento copertina: {e}")
        else:
            placeholder = PhotoImage(width=640, height=640)
            self.cover_label.configure(image=placeholder, text="Copertina non trovata",
                                       fg=settings.TEXT_COLOR, compound='center')
            self.cover_label.image = placeholder

        # Aggiorna selezione lista
        self.song_box.selection_clear(0, 'end')
        self.song_box.selection_set(index)
        self.song_box.activate(index)
        self.song_box.see(index)

    def toggle_play_pause(self):
        """Pulsante play/pausa."""
        self.player.toggle_pause()
        new_text = "▶" if self.player.is_paused else "⏸"
        self.play_pause_button.config(text=new_text)

    def toggle_shuffle_ui(self):
        """Attiva/disattiva shuffle e aggiorna il colore del bottone."""
        self.player.toggle_shuffle()
        new_color = settings.PRIMARY_COLOR if self.player.shuffle else settings.TEXT_COLOR
        # Cerca e aggiorna il bottone shuffle
        for widget in self.root.winfo_children():
            for subwidget in widget.winfo_children():
                if isinstance(subwidget, Button) and subwidget.cget("text") == "🔀":
                    subwidget.config(fg=new_color)

    def update_progress(self):
        """Aggiorna la barra di progresso e il tempo."""
        if self.player.running:
            current_ms = self.player.player.get_time()
            total_ms = self.player.player.get_length()
            self.time_var.set(f"{utils.format_time(current_ms)} / {utils.format_time(total_ms)}")
            self.progress_bar['value'] = (current_ms / total_ms) * 100 if total_ms > 0 else 0
            self.root.after(500, self.update_progress)

    def on_close(self):
        """Chiusura applicazione."""
        self.player.shutdown()
        self.db_conn.close()
        self.root.destroy()


# === Avvio Applicazione ===
def main():
    root = Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
