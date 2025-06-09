import os
import json
import threading
import yt_dlp
from urllib.parse import urlparse

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

# Set window size for desktop testing
if platform not in ['android', 'ios']:
    Window.size = (400, 700)

class MediaCatcherApp(App):
    def build(self):
        self.title = 'Media Catcher'
        self.icon = 'media-catcher.png'
        
        # Main layout
        self.main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.main_layout.bind(size=self._update_background)
        
        # Set background color
        with self.main_layout.canvas.before:
            Color(0.1, 0.1, 0.2, 1)  # Dark blue background
            self.rect = Rectangle(size=self.main_layout.size, pos=self.main_layout.pos)
        
        # Title
        title = Label(
            text='Media Catcher',
            size_hint=(1, 0.1),
            font_size='24sp',
            bold=True
        )
        self.main_layout.add_widget(title)
        
        # URL Input
        self.url_input = TextInput(
            hint_text='Enter URL(s) here...',
            multiline=True,
            size_hint=(1, 0.2),
            background_color=(0.2, 0.2, 0.3, 1),
            foreground_color=(1, 1, 1, 1)
        )
        self.main_layout.add_widget(self.url_input)
        
        # Mode selection
        mode_layout = BoxLayout(size_hint=(1, 0.08), spacing=10)
        mode_label = Label(text='Mode:', size_hint=(0.3, 1))
        self.mode_spinner = Spinner(
            text='Audio',
            values=('Audio', 'Video'),
            size_hint=(0.7, 1),
            background_color=(0.3, 0.3, 0.4, 1)
        )
        self.mode_spinner.bind(text=self.on_mode_change)
        mode_layout.add_widget(mode_label)
        mode_layout.add_widget(self.mode_spinner)
        self.main_layout.add_widget(mode_layout)
        
        # Playlist checkbox
        playlist_layout = BoxLayout(size_hint=(1, 0.08))
        self.playlist_check = CheckBox(size_hint=(0.1, 1))
        playlist_label = Label(text='Download entire playlist', size_hint=(0.9, 1))
        playlist_layout.add_widget(self.playlist_check)
        playlist_layout.add_widget(playlist_label)
        self.main_layout.add_widget(playlist_layout)
        
        # Audio options
        self.audio_options = BoxLayout(orientation='vertical', size_hint=(1, 0.16), spacing=5)
        
        # Audio format
        audio_format_layout = BoxLayout(size_hint=(1, 0.5))
        audio_format_label = Label(text='Format:', size_hint=(0.3, 1))
        self.audio_format_spinner = Spinner(
            text='mp3',
            values=('mp3', 'wav', 'aac'),
            size_hint=(0.7, 1),
            background_color=(0.3, 0.3, 0.4, 1)
        )
        audio_format_layout.add_widget(audio_format_label)
        audio_format_layout.add_widget(self.audio_format_spinner)
        self.audio_options.add_widget(audio_format_layout)
        
        # Audio quality
        audio_quality_layout = BoxLayout(size_hint=(1, 0.5))
        audio_quality_label = Label(text='Quality:', size_hint=(0.3, 1))
        self.audio_quality_spinner = Spinner(
            text='192K',
            values=('320K', '192K', '128K', '64K'),
            size_hint=(0.7, 1),
            background_color=(0.3, 0.3, 0.4, 1)
        )
        audio_quality_layout.add_widget(audio_quality_label)
        audio_quality_layout.add_widget(self.audio_quality_spinner)
        self.audio_options.add_widget(audio_quality_layout)
        
        self.main_layout.add_widget(self.audio_options)
        
        # Video options (hidden by default) - UPRAVENÉ: odstránené titulky
        self.video_options = BoxLayout(orientation='vertical', size_hint=(1, 0.08), spacing=5)
        
        # Video quality
        video_quality_layout = BoxLayout(size_hint=(1, 1))
        video_quality_label = Label(text='Quality:', size_hint=(0.3, 1))
        self.video_quality_spinner = Spinner(
            text='Best',
            values=('Best', '1080p', '720p', '480p', '360p', '240p'),
            size_hint=(0.7, 1),
            background_color=(0.3, 0.3, 0.4, 1)
        )
        video_quality_layout.add_widget(video_quality_label)
        video_quality_layout.add_widget(self.video_quality_spinner)
        self.video_options.add_widget(video_quality_layout)
        
        # Don't add video options initially
        
        # Output folder button
        self.output_dir = self.get_default_download_dir()
        self.folder_button = Button(
            text=f'Output: {os.path.basename(self.output_dir)}',
            size_hint=(1, 0.08),
            background_color=(0.3, 0.3, 0.4, 1)
        )
        self.folder_button.bind(on_press=self.choose_folder)
        self.main_layout.add_widget(self.folder_button)
        
        # Buttons
        buttons_layout = BoxLayout(size_hint=(1, 0.08), spacing=10)
        
        self.download_button = Button(
            text='Download',
            background_color=(0.2, 0.6, 0.2, 1)
        )
        self.download_button.bind(on_press=self.start_download)
        
        self.stop_button = Button(
            text='Stop',
            background_color=(0.6, 0.2, 0.2, 1),
            disabled=True
        )
        # Poznámka: stop_download nebude fungovať na prerušenie už prebiehajúceho sťahovania,
        # ale zabráni spusteniu ďalšieho v poradí.
        self.stop_button.bind(on_press=self.stop_download)
        
        self.clear_button = Button(
            text='Clear',
            background_color=(0.4, 0.4, 0.4, 1)
        )
        self.clear_button.bind(on_press=self.clear_fields)
        
        buttons_layout.add_widget(self.download_button)
        buttons_layout.add_widget(self.stop_button)
        buttons_layout.add_widget(self.clear_button)
        self.main_layout.add_widget(buttons_layout)
        
        # Progress bar
        self.progress_bar = ProgressBar(
            max=100,
            size_hint=(1, 0.05)
        )
        self.main_layout.add_widget(self.progress_bar)
        
        # Status label
        self.status_label = Label(
            text='Ready',
            size_hint=(1, 0.08)
        )
        self.main_layout.add_widget(self.status_label)
        
        # Initialize
        self.current_process = None # Už sa nepoužíva pre subprocess
        self.is_downloading = False
        
        return self.main_layout
    
    def _update_background(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def get_default_download_dir(self):
        if platform == 'android':
            # Na Androide je potrebné získať povolenie na zápis
            # Toto je zjednodušený príklad, reálna aplikácia by mala riešiť
            # požiadavku na povolenie (request_permissions)
            from android.storage import primary_external_storage_path
            download_dir = os.path.join(primary_external_storage_path(), 'Download')
            return download_dir
        else:
            return os.path.expanduser('~/Downloads')
    
    def on_mode_change(self, spinner, text):
        if text == 'Audio':
            if self.video_options in self.main_layout.children:
                self.main_layout.remove_widget(self.video_options)
            if self.audio_options not in self.main_layout.children:
                # Find the position to insert
                index = self.main_layout.children.index(self.folder_button) + 1
                self.main_layout.add_widget(self.audio_options, index)
        else:
            if self.audio_options in self.main_layout.children:
                self.main_layout.remove_widget(self.audio_options)
            if self.video_options not in self.main_layout.children:
                # Find the position to insert
                index = self.main_layout.children.index(self.folder_button) + 1
                self.main_layout.add_widget(self.video_options, index)
    
    def choose_folder(self, instance):
        content = BoxLayout(orientation='vertical')
        
        # File chooser
        filechooser = FileChooserListView(
            path=self.output_dir,
            dirselect=True,
            size_hint=(1, 0.9)
        )
        content.add_widget(filechooser)
        
        # Buttons
        buttons = BoxLayout(size_hint=(1, 0.1))
        
        select_btn = Button(text='Select')
        cancel_btn = Button(text='Cancel')
        
        buttons.add_widget(select_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)
        
        # Popup
        popup = Popup(
            title='Choose Output Folder',
            content=content,
            size_hint=(0.9, 0.9)
        )
        
        def on_select(instance):
            if filechooser.selection:
                self.output_dir = filechooser.selection[0]
                self.folder_button.text = f'Output: {os.path.basename(self.output_dir)}'
            popup.dismiss()
        
        select_btn.bind(on_press=on_select)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def clear_fields(self, instance):
        self.url_input.text = ''
        self.progress_bar.value = 0
        self.status_label.text = 'Ready'
    
    def start_download(self, instance):
        urls = self.url_input.text.strip()
        if not urls:
            self.show_error('Please enter a URL')
            return
        
        self.is_downloading = True
        self.download_button.disabled = True
        self.stop_button.disabled = False
        self.status_label.text = 'Starting download...'
        
        # Start download in thread
        thread = threading.Thread(target=self.download_thread, args=(urls,))
        thread.daemon = True
        thread.start()
    
    def stop_download(self, instance):
        # Táto funkcia už nemôže priamo zastaviť yt-dlp, lebo nebeží ako subprocess.
        # Namiesto toho nastaví 'is_downloading' na False, čo zabráni sťahovaniu
        # ďalšej položky v zozname URL adries.
        self.is_downloading = False
        self.download_button.disabled = False
        self.stop_button.disabled = True
        self.status_label.text = 'Stopping...'
    
    # --- PREPÍSANÁ FUNKCIA ---
    def download_thread(self, urls):
        try:
            url_list = [url.strip() for url in urls.split('\n') if url.strip()]

            # Funkcia (hook), ktorá bude aktualizovať progress bar a status label
            def my_hook(d):
                if not self.is_downloading:
                    # Ak bol stlačný Stop, vyvolá chybu na prerušenie
                    raise yt_dlp.utils.DownloadCancelled()

                if d['status'] == 'downloading':
                    # Odstráneme percentuálny znak a prekonvertujeme na číslo
                    p_str = d.get('_percent_str', '0.0%').replace('%', '').strip()
                    try:
                        p = float(p_str)
                        # Aktualizujeme UI prvky bezpečne z vlákna pomocou Clock
                        Clock.schedule_once(lambda dt, prog=p: setattr(self.progress_bar, 'value', prog))
                        Clock.schedule_once(lambda dt, prog=p: setattr(self.status_label, 'text', f'Downloading... {prog:.1f}%'))
                    except ValueError:
                        pass # Ignorujeme, ak sa percentá nedajú prečítať
                
                elif d['status'] == 'finished':
                    Clock.schedule_once(lambda dt: setattr(self.progress_bar, 'value', 100))
                    Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 'Download complete!'))

            for url in url_list:
                if not self.is_downloading:
                    break

                # Pripravíme možnosti pre yt-dlp ako slovník
                output_path = os.path.join(self.output_dir, '%(title)s.%(ext)s')
                ydl_opts = {
                    'outtmpl': output_path,
                    'progress_hooks': [my_hook],
                    'noplaylist': not self.playlist_check.active,
                    'playlist_items': '1' if not self.playlist_check.active else None,
                    # Pridané pre lepšiu kompatibilitu na Androide
                    'nocheckcertificate': True, 
                }

                # Možnosti pre audio
                if self.mode_spinner.text == 'Audio':
                    audio_format = self.audio_format_spinner.text
                    audio_quality = self.audio_quality_spinner.text.replace('K', '')
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': audio_format,
                        'preferredquality': audio_quality,
                    }]
                # Možnosti pre video - UPRAVENÉ: odstránené titulky
                else:
                    quality = self.video_quality_spinner.text
                    format_code = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                    if quality != 'Best':
                         height = quality.replace('p','')
                         format_code = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                    
                    ydl_opts['format'] = format_code
                    ydl_opts['merge_output_format'] = 'mp4'
                
                # Spustenie sťahovania priamo cez knižnicu
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

        except yt_dlp.utils.DownloadCancelled:
            self.status_label.text = 'Download stopped'
        except Exception as e:
            Clock.schedule_once(lambda dt, err=str(e): self.show_error(f"Error: {err}"))
        finally:
            Clock.schedule_once(lambda dt: self.download_finished())

    def download_finished(self, *args):
        self.is_downloading = False
        self.download_button.disabled = False
        self.stop_button.disabled = True
    
    def show_error(self, message):
        popup = Popup(
            title='Error',
            content=Label(text=message),
            size_hint=(0.8, 0.4) # Zväčšil som popup pre lepšiu čitateľnosť chýb
        )
        popup.open()

    def on_pause(self):
        # Handle app pause (Android)
        return True
    
    def on_resume(self):
        # Handle app resume (Android)
        pass

if __name__ == '__main__':
    MediaCatcherApp().run()
    
    
        
    
    # Media Catcher
# Copyright (C) 2024 Markus Aureus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
