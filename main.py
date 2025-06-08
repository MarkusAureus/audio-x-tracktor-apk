import os
import json
import threading
import subprocess
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
        
        # Video options (hidden by default)
        self.video_options = BoxLayout(orientation='vertical', size_hint=(1, 0.24), spacing=5)
        
        # Video quality
        video_quality_layout = BoxLayout(size_hint=(1, 0.33))
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
        
        # Subtitles checkbox
        subtitles_layout = BoxLayout(size_hint=(1, 0.33))
        self.subtitles_check = CheckBox(size_hint=(0.1, 1))
        subtitles_label = Label(text='Download subtitles', size_hint=(0.9, 1))
        subtitles_layout.add_widget(self.subtitles_check)
        subtitles_layout.add_widget(subtitles_label)
        self.video_options.add_widget(subtitles_layout)
        
        # Subtitle language
        sub_lang_layout = BoxLayout(size_hint=(1, 0.33))
        sub_lang_label = Label(text='Language:', size_hint=(0.3, 1))
        self.sub_lang_spinner = Spinner(
            text='en',
            values=('en', 'sk', 'cs', 'de', 'fr', 'es'),
            size_hint=(0.7, 1),
            background_color=(0.3, 0.3, 0.4, 1)
        )
        sub_lang_layout.add_widget(sub_lang_label)
        sub_lang_layout.add_widget(self.sub_lang_spinner)
        self.video_options.add_widget(sub_lang_layout)
        
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
        self.current_process = None
        self.is_downloading = False
        
        return self.main_layout
    
    def _update_background(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def get_default_download_dir(self):
        if platform == 'android':
            from android.storage import primary_external_storage_path
            return os.path.join(primary_external_storage_path(), 'Download')
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
        if self.current_process:
            self.current_process.terminate()
        self.is_downloading = False
        self.download_button.disabled = False
        self.stop_button.disabled = True
        self.status_label.text = 'Download stopped'
        self.progress_bar.value = 0
    
    def download_thread(self, urls):
        try:
            import re
            
            url_list = [url.strip() for url in urls.split('\n') if url.strip()]
            
            for url in url_list:
                if not self.is_downloading:
                    break
                
                # Prepare yt-dlp command
                cmd = ['yt-dlp', url, '--newline']
                
                # Output path
                output_path = os.path.join(self.output_dir, '%(title)s.%(ext)s')
                cmd.extend(['-o', output_path])
                
                # Mode specific options
                if self.mode_spinner.text == 'Audio':
                    audio_format = self.audio_format_spinner.text
                    cmd.extend(['-x', '--audio-format', audio_format])
                    
                    if audio_format in ['mp3', 'aac']:
                        quality = self.audio_quality_spinner.text
                        quality_map = {'320K': '0', '192K': '2', '128K': '5', '64K': '9'}
                        cmd.extend(['--audio-quality', quality_map.get(quality, '2')])
                else:
                    # Video mode
                    cmd.extend(['--merge-output-format', 'mp4'])
                    
                    quality = self.video_quality_spinner.text
                    if quality == 'Best':
                        cmd.extend(['-f', 'bestvideo+bestaudio'])
                    else:
                        # Map quality to format codes
                        quality_map = {
                            '1080p': '137+140',
                            '720p': '136+140', 
                            '480p': '135+140',
                            '360p': '134+140',
                            '240p': '133+140'
                        }
                        format_code = quality_map.get(quality, 'best')
                        cmd.extend(['-f', format_code])
                    
                    # Subtitles
                    if self.subtitles_check.active:
                        sub_lang = self.sub_lang_spinner.text
                        cmd.extend(['--write-auto-sub', '--sub-lang', sub_lang, 
                                  '--convert-subs', 'srt'])
                
                # Playlist handling
                if not self.playlist_check.active:
                    cmd.extend(['--playlist-items', '1'])
                
                # Execute download
                self.current_process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                
                # Parse output for progress
                for line in self.current_process.stdout:
                    if not self.is_downloading:
                        self.current_process.terminate()
                        break
                    
                    # Extract progress percentage
                    match = re.search(r'\[download\]\s+(\d+\.?\d*)%', line)
                    if match:
                        progress = float(match.group(1))
                        Clock.schedule_once(
                            lambda dt, p=progress: setattr(self.progress_bar, 'value', p)
                        )
                        Clock.schedule_once(
                            lambda dt, p=progress: setattr(
                                self.status_label, 'text', f'Downloading... {p:.1f}%'
                            )
                        )
                    
                    # Check for completion
                    if '[download] 100%' in line or 'has already been downloaded' in line:
                        Clock.schedule_once(
                            lambda dt: setattr(self.progress_bar, 'value', 100)
                        )
                
                # Wait for process to complete
                self.current_process.wait()
                
                if self.current_process.returncode == 0:
                    Clock.schedule_once(
                        lambda dt: setattr(self.status_label, 'text', 'Download complete!')
                    )
                else:
                    stderr = self.current_process.stderr.read()
                    Clock.schedule_once(
                        lambda dt, err=stderr: self.show_error(f'Download failed: {err[:100]}')
                    )
                    
        except FileNotFoundError:
            Clock.schedule_once(
                lambda dt: self.show_error('yt-dlp not found. Please install it first.')
            )
        except Exception as e:
            Clock.schedule_once(lambda dt, err=str(e): self.show_error(err))
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
            size_hint=(0.8, 0.3)
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
