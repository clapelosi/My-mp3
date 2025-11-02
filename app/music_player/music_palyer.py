#!/usr/bin/env python3
import os
import sys
import time
import vlc
import random


# Importa le impostazioni e le utilità del progetto
from app import settings
from app import utils



class MusicPlayer:
    def __init__(self, on_song_change_callback=None):

        # player è il vlc
        self.player = vlc.MediaPlayer()

        # set empty playlist array
        self.playlist = []  # Lista di tuple (file_path, titolo, cover_path)
        ## ->> ci aggiungiamo artist
        # -> # Lista di tuple (file_path, titolo, artits, cover_path)

        self.current_index = -1
        self.running = True
        self.is_paused = False
        self.shuffle = False  # ✅ inizializzato
        self.on_song_change = on_song_change_callback
        self.played_song_cache = set()


    def load_playlist(self, songs):
        """Carica una nuova playlist di canzoni."""
        self.stop()
        self.playlist = songs # -> songs preso da ui box
        self.current_index = -1
        self.played_song_cache.clear()
        self.play_song_at_index(0)

    def play_song_at_index(self, index):
        if 0 <= index < len(self.playlist):
            self.current_index = index
            self.play_current()

    def next_track(self):
        """Passa alla canzone successiva (supporta shuffle)."""
        if not self.playlist:
            return

        if self.shuffle:
            unplayed_songs = [i for i in range(len(self.playlist)) if i not in self.played_song_cache]
            if not unplayed_songs:
                self.played_song_cache.clear()
                unplayed_songs = list(range(len(self.playlist)))
            
            self.current_index = random.choice(unplayed_songs)
            self.played_song_cache.add(self.current_index)
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

        # se non è settata la plaulist di canzoni oppure
        # il current index è -1 non fa niente
        if not self.playlist or not (0 <= self.current_index < len(self.playlist)):
            return
        
        self.played_song_cache.add(self.current_index)

        # definisce il cazzo di entry
        entry = self.playlist[self.current_index]

        # se la lughezza dell'entry è pari a due setta cover_path none
        if len(entry) == 2:
            file_path, song_title = entry
            cover_path = None

        elif len(entry) >= 4:
            file_path, song_title, cover_path, artists = entry[:4]

        # diversemnte prende i primi 3 
        elif len(entry) >= 3:
            file_path, song_title, cover_path = entry[:3]
        else:
            print("Formato playlist non valido:", entry)
            return

        if not os.path.exists(file_path):
            print(f"Errore: file non trovato -> {file_path}")
            self.next_track()
            return

        # prendi la cazzo di canzone dal file path
        media = vlc.Media(file_path)
        # la setta
        self.player.set_media(media)
        # suonala 
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
        self.played_song_cache.clear()
        print(f"Modalità shuffle: {'attiva' if self.shuffle else 'disattivata'}")

    def stop(self):
        self.player.stop()

    def set_volume(self, volume):
        """Imposta il volume (0-100)."""
        self.player.audio_set_volume(int(float(volume)))

    def set_position(self, position):
        """Sposta la posizione di riproduzione a un punto specifico (0.0 a 1.0)."""
        if self.player.is_seekable():
            # Assicura che la posizione sia nel range valido
            position = max(0.0, min(1.0, position))
            self.player.set_position(position)

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
