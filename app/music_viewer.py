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

# Add the project root to the Python path to resolve imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importa le impostazioni e le utilità del progetto
from app import settings
from app import utils

import random


# === Classe per la Logica di Riproduzione ===

class MusicPlayer:
    def __init__(self, on_song_change_callback=None):
        self.player = vlc.MediaPlayer()
        self.playlist = [] # La playlist ora è una lista di tuple (song_path, song_title)
        self.current_index = -1
        self.running = True
        self.is_paused = False
        self.on_song_change = on_song_change_callback

    def load_playlist(self, songs):
        """Carica una nuova playlist di canzoni."""
        self.stop() # Ferma la riproduzione corrente
        self.playlist = songs
        self.current_index = 0
        self.play_current()

    def play_song_at_index(self, index):
        if 0 <= index < len(self.playlist):
            self.current_index = index
            self.play_current()
    
    def next_track(self):
        if not self.playlist:
            return

        if self.shuffle:
            self.current_index = random.randint(0, len(self.playlist) - 1)
        else:
            self.current_index = (self.current_index + 1) % len(self.playlist)

        self.play_current()

    def play_current(self):
        if not self.playlist or not (0 <= self.current_index < len(self.playlist)):
            return
        
        # file_path, song_title = self.playlist[self.current_index]
        # Supporta playlist con o senza cover_path
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
            self.next_track() # Prova la canzone successiva
            return

        media = vlc.Media(file_path)
        self.player.set_media(media)
        self.player.play()
        self.is_paused = False
        if self.on_song_change:
            self.on_song_change(file_path, song_title, self.current_index)

    def toggle_pause(self):
        if self.player.is_playing():
            self.player.pause()
            self.is_paused = True
        else:
            self.player.pause()
            self.is_paused = False
    
    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        print(f"Modalità shuffle: {'attiva' if self.shuffle else 'disattivata'}")
    
    def toggle_shuffle_ui(self):
        self.player.toggle_shuffle()
        new_color = settings.PRIMARY_COLOR if self.player.shuffle else settings.TEXT_COLOR
        self.root.update_idletasks()
        # Cambia il colore del bottone per indicare stato attivo
        for widget in self.root.winfo_children():
            if isinstance(widget, Button) and widget.cget("text") == "🔀":
                widget.config(fg=new_color)


    def next_track(self):
        if not self.playlist: return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play_current()

    def prev_track(self):
        if not self.playlist: return
        self.current_index = (self.current_index - 1 + len(self.playlist)) % len(self.playlist)
        self.play_current()

    def stop(self):
        self.player.stop()

    def set_volume(self, volume):
        self.player.audio_set_volume(int(float(volume)))

    def shutdown(self):
        self.stop()
        self.running = False

    def run_playlist_monitor(self):
        """Loop che monitora la fine di una canzone per passare alla successiva."""
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
        self.playlists = [] # Lista di tuple (id, name)

        self.player = MusicPlayer(self.update_ui_for_song)
        
        self.setup_styles()
        self.create_widgets()
        self.load_playlists_from_db()

        self.playback_thread = threading.Thread(target=self.player.run_playlist_monitor, daemon=True)
        self.playback_thread.start()

        self.update_progress()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("dark.Horizontal.TProgressbar", troughcolor=settings.COMPONENT_BACKGROUND, background=settings.PRIMARY_COLOR, bordercolor=settings.BACKGROUND_COLOR)
        style.configure("dark.Horizontal.TScale", troughcolor=settings.COMPONENT_BACKGROUND, background=settings.PRIMARY_COLOR, bordercolor=settings.BACKGROUND_COLOR)
        style.configure("TLabel", background=settings.BACKGROUND_COLOR, foreground=settings.TEXT_COLOR)
        style.configure("TFrame", background=settings.BACKGROUND_COLOR)

    def create_widgets(self):
        main_frame = Frame(self.root, bg=settings.BACKGROUND_COLOR)
        main_frame.pack(padx=10, pady=10, fill='both', expand=True)

        # OLD --- COLONNA SINISTRA (Player) ---
        # left_frame = Frame(main_frame, bg=settings.BACKGROUND_COLOR)
        # left_frame.pack(side='left', fill='y', padx=(0, 10))
        
        # self.cover_label = Label(left_frame, bg=settings.BACKGROUND_COLOR, width=42, height=21) # Placeholder size
        # self.cover_label.pack(pady=10)
        # --- COLONNA SINISTRA (Player) ---
        left_frame = Frame(main_frame, bg=settings.BACKGROUND_COLOR)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))  # fill both + expand

        # Usa un frame per la copertina con fill & expand
        cover_frame = Frame(left_frame, bg=settings.BACKGROUND_COLOR)
        cover_frame.pack(pady=10, fill='both', expand=True)

        self.cover_label = Label(cover_frame, bg=settings.BACKGROUND_COLOR)
        self.cover_label.pack(fill='both', expand=True)


        info_frame = Frame(left_frame, bg=settings.BACKGROUND_COLOR)
        info_frame.pack(pady=5, fill='x')
        self.song_title_var = StringVar(value="Nessuna canzone in riproduzione")
        Label(info_frame, textvariable=self.song_title_var, fg=settings.TEXT_COLOR, bg=settings.BACKGROUND_COLOR, font=(settings.FONT_FAMILY, settings.FONT_SIZE_TITLE)).pack()
        self.time_var = StringVar(value="--:-- / --:--")
        Label(info_frame, textvariable=self.time_var, fg=settings.MUTED_TEXT_COLOR, bg=settings.BACKGROUND_COLOR, font=(settings.FONT_FAMILY, settings.FONT_SIZE_TIME)).pack()
        self.progress_bar = ttk.Progressbar(info_frame, orient='horizontal', mode='determinate', style="dark.Horizontal.TProgressbar")
        self.progress_bar.pack(pady=5, fill='x', expand=True)

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
        self.play_pause_button = Button(controls_frame, text="▶", font=button_font, command=self.toggle_play_pause, **button_config)
        self.play_pause_button.grid(row=0, column=1, padx=5)
        Button(controls_frame, text="⏭", font=button_font, command=self.player.next_track, **button_config).grid(row=0, column=2, padx=5)
        Button(controls_frame, text="⏹", font=button_font, command=self.player.stop, **button_config).grid(row=0, column=3, padx=5)
        Button(
            controls_frame, text="🔀", font=button_font,
            command=self.toggle_shuffle_ui, **button_config
        ).grid(row=0, column=4, padx=5)
        volume_frame = Frame(left_frame, bg=settings.BACKGROUND_COLOR)
        volume_frame.pack(pady=5, fill='x')
        Label(volume_frame, text="🔉", bg=settings.BACKGROUND_COLOR, fg=settings.TEXT_COLOR, font=(settings.FONT_FAMILY, 12)).pack(side='left')
        self.volume_slider = ttk.Scale(volume_frame, from_=0, to=100, orient='horizontal', command=self.player.set_volume, style="dark.Horizontal.TScale")
        self.volume_slider.set(100)
        self.volume_slider.pack(side='left', fill='x', expand=True, padx=5)
        Label(volume_frame, text="🔊", bg=settings.BACKGROUND_COLOR, fg=settings.TEXT_COLOR, font=(settings.FONT_FAMILY, 12)).pack(side='left')

        # --- COLONNA DESTRA (PlaylistS & Canzoni) ---
        right_frame = Frame(main_frame, bg=settings.BACKGROUND_COLOR, width=250) # Larghezza ridotta
        right_frame.pack(side='right', fill='y', expand=False, padx=(10, 0))
        right_frame.pack_propagate(False) # Impedisce al frame di ridimensionarsi

        paned_window = ttk.PanedWindow(right_frame, orient='vertical')
        paned_window.pack(fill='both', expand=True)

        # Frame per le playlist
        playlist_frame = Frame(paned_window, bg=settings.BACKGROUND_COLOR)
        Label(playlist_frame, text="Playlists 📜", font=(settings.FONT_FAMILY, 14), fg=settings.TEXT_COLOR, bg=settings.BACKGROUND_COLOR).pack(pady=(0, 5))
        
        playlist_container = Frame(playlist_frame)
        playlist_container.pack(fill='both', expand=True)
        
        self.playlist_box = Listbox(playlist_container, bg=settings.COMPONENT_BACKGROUND, fg=settings.TEXT_COLOR, selectbackground=settings.PRIMARY_COLOR, highlightthickness=0, border=0, font=(settings.FONT_FAMILY, settings.FONT_SIZE_PLAYLIST), exportselection=False)
        self.playlist_box.pack(side='left', fill='both', expand=True)
        self.playlist_box.bind("<Double-1>", self.load_songs_for_playlist)
        
        scrollbar_playlist = Scrollbar(playlist_container, orient='vertical', command=self.playlist_box.yview)
        scrollbar_playlist.pack(side='right', fill='y')
        self.playlist_box.config(yscrollcommand=scrollbar_playlist.set)
        
        paned_window.add(playlist_frame, weight=1)

        # Frame per le canzoni
        songs_frame = Frame(paned_window, bg=settings.BACKGROUND_COLOR)
        Label(songs_frame, text="Canzoni 🎵", font=(settings.FONT_FAMILY, 14), fg=settings.TEXT_COLOR, bg=settings.BACKGROUND_COLOR).pack(pady=(0, 5))

        songs_container = Frame(songs_frame)
        songs_container.pack(fill='both', expand=True)

        self.song_box = Listbox(songs_container, bg=settings.COMPONENT_BACKGROUND, fg=settings.TEXT_COLOR, selectbackground=settings.PRIMARY_COLOR, highlightthickness=0, border=0, font=(settings.FONT_FAMILY, settings.FONT_SIZE_PLAYLIST), exportselection=False)
        self.song_box.pack(side='left', fill='both', expand=True)
        self.song_box.bind("<Double-1>", self.play_selected_song)

        scrollbar_songs = Scrollbar(songs_container, orient='vertical', command=self.song_box.yview)
        scrollbar_songs.pack(side='right', fill='y')
        self.song_box.config(yscrollcommand=scrollbar_songs.set)

        paned_window.add(songs_frame, weight=2)

    def load_playlists_from_db(self):
        """Carica i nomi delle playlist dal database e li mostra nella Listbox."""
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
        selected_indices = self.playlist_box.curselection()
        if not selected_indices:
            return
        
        selected_playlist_index = selected_indices[0]
        playlist_id, playlist_name = self.playlists[selected_playlist_index]
        
        print(f"Caricamento canzoni per playlist: {playlist_name} (ID: {playlist_id})")
        
        try:
            cursor = self.db_conn.cursor() # copertina_640_path
            cursor.execute("""
                SELECT s.song_id, s.title, s.mp4_path, s.copertina_640_path as cover_path
                FROM songs s
                JOIN playlist_songs ps ON s.song_id = ps.song_id
                WHERE ps.playlist_id = ?
            """, (playlist_id,))
            
            self.current_song_list = cursor.fetchall()
            self.song_box.delete(0, 'end')
            
            if self.current_song_list:
                #for _, title, _ in self.current_song_list:
                 #   self.song_box.insert('end', title)
                for song_id, title, mp4_path, copertina_path in self.current_song_list:
                    self.song_box.insert('end', title)

            else:
                print(f"Nessuna canzone trovata per la playlist '{playlist_name}'")

        except Exception as e:
            print(f"Errore nel caricare le canzoni della playlist: {e}")

    def play_selected_song(self, event=None):
        selected_indices = self.song_box.curselection()
        if not selected_indices:
            return
        
        song_index_in_list = selected_indices[0]
        
        # Prepara la playlist per il player (path, titolo, cover_path)
        songs_for_player = [(song[2], song[1], song[3]) for song in self.current_song_list]
        
        self.player.load_playlist(songs_for_player)
        self.player.play_song_at_index(song_index_in_list)


    def update_ui_for_song(self, file_path, song_title, index):
        # Titolo
        self.song_title_var.set(song_title)

        # Copertina
        cover_path = None
        if hasattr(self, 'current_song_list') and 0 <= index < len(self.current_song_list):
            # self.current_song_list ora è una lista di tuple (song_id, title, mp4_path, cover_path)
            cover_path = self.current_song_list[index][3]
        '''
        if cover_path and os.path.exists(cover_path):
            try:
                img = Image.open(cover_path)
                img.thumbnail((640, 640))
                cover_img = ImageTk.PhotoImage(img)
                
                self.cover_label.configure(image=cover_img)
                self.cover_label.image = cover_img
            except Exception as e:
                print(f"Errore nel caricamento della copertina: {e}")
                # Mostra un placeholder in caso di errore
                placeholder = PhotoImage(width=640, height=640)
                self.cover_label.configure(image=placeholder, text="Errore Copertina", fg=settings.TEXT_COLOR, compound='center')
                self.cover_label.image = placeholder
        '''
        if cover_path and os.path.exists(cover_path):
            try:
                img = Image.open(cover_path)
                # Scala dinamicamente in base alle dimensioni attuali della label
                label_width = self.cover_label.winfo_width() or 640
                label_height = self.cover_label.winfo_height() or 640
                img.thumbnail((label_width, label_height))
                cover_img = ImageTk.PhotoImage(img)
                
                self.cover_label.configure(image=cover_img)
                self.cover_label.image = cover_img
            except Exception as e:
                print(f"Errore nel caricamento della copertina: {e}")

        else:
            # Se non c'è un percorso o il file non esiste, mostra un placeholder
            placeholder = PhotoImage(width=640, height=640)
            self.cover_label.configure(image=placeholder, text="Copertina non trovata", fg=settings.TEXT_COLOR, compound='center')
            self.cover_label.image = placeholder
        
        # Aggiorna la selezione nella lista delle canzoni
        if hasattr(self, 'song_box'):
            self.song_box.selection_clear(0, 'end')
            self.song_box.selection_set(index)
            self.song_box.activate(index)
            self.song_box.see(index)

    def toggle_play_pause(self):
        self.player.toggle_pause()
        new_text = "▶" if self.player.is_paused else "⏸"
        self.play_pause_button.config(text=new_text)


    def update_progress(self):
        if self.player.running:
            current_time_ms = self.player.player.get_time()
            total_time_ms = self.player.player.get_length()
            self.time_var.set(f"{utils.format_time(current_time_ms)} / {utils.format_time(total_time_ms)}")
            if total_time_ms > 0:
                self.progress_bar['value'] = (current_time_ms / total_time_ms) * 100
            else:
                self.progress_bar['value'] = 0
            self.root.after(500, self.update_progress)

    def on_close(self):
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
