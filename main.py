import os
import sys
import threading
import yt_dlp
from urllib.parse import urlparse, parse_qsl

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.clock import Clock
from kivy.utils import platform, get_color_from_hex
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.scrollview import ScrollView
from kivy.storage.jsonstore import JsonStore
from kivy.uix.image import Image

if platform not in ['android', 'ios']:
    Window.size = (400, 700)

class DummyStream:
    def write(self, *args, **kwargs):
        pass
    def flush(self, *args, **kwargs):
        pass

class AudioXtractorApp(App):

    def build(self):
        self.themes = {
            'Dark Knight': {
                'bg': [0.1, 0.1, 0.2, 1], 'text': [1, 1, 1, 1],
                'input_bg': [0.2, 0.2, 0.3, 1], 'button_bg': [0.3, 0.3, 0.4, 1],
                'primary_button_bg': [0.2, 0.6, 0.2, 1]
            },
            'Arctic Light': {
                'bg': [0.95, 0.95, 1, 1], 'text': [0, 0, 0, 1],
                'input_bg': [1, 1, 1, 1], 'button_bg': [0.8, 0.85, 0.9, 1],
                'primary_button_bg': [0.3, 0.7, 0.3, 1]
            },
            'Ocean Blue': {
                'bg': get_color_from_hex('#003B46'), 'text': get_color_from_hex('#EFEFEF'),
                'input_bg': get_color_from_hex('#07575B'), 'button_bg': get_color_from_hex('#66A5AD'),
                'primary_button_bg': get_color_from_hex('#C4DFE6')
            },
            'Sunset Orange': {
                'bg': get_color_from_hex('#333333'), 'text': get_color_from_hex('#FFFFFF'),
                'input_bg': get_color_from_hex('#555555'), 'button_bg': get_color_from_hex('#D95D39'),
                'primary_button_bg': get_color_from_hex('#F0A202')
            }
        }
        self.store = JsonStore('settings.json')
        
        self.title = 'Audio X-tracktor'
        self.icon = 'icon.png'
        
        self.main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.main_layout.bind(size=self._update_background)
        
        with self.main_layout.canvas.before:
            self.bg_color = Color(0,0,0,1)
            self.rect = Rectangle(size=self.main_layout.size, pos=self.main_layout.pos)
        
        logo_image = Image(
            source='logo.png',
            size_hint=(1, 0.15),
            allow_stretch=True,
            keep_ratio=True
        )
        self.main_layout.add_widget(logo_image)
        
        self.url_input = TextInput(
            hint_text='Enter URL(s) here...', multiline=True, size_hint=(1, 0.3),
            background_color=(0.2, 0.2, 0.3, 1), foreground_color=(1, 1, 1, 1)
        )
        self.main_layout.add_widget(self.url_input)
        
        playlist_layout = BoxLayout(size_hint=(1, 0.08))
        self.playlist_check = CheckBox(size_hint=(0.1, 1), color=[1,1,1,1])
        self.playlist_label = Label(text='Download entire playlist', size_hint=(0.9, 1))
        playlist_layout.add_widget(self.playlist_check)
        playlist_layout.add_widget(self.playlist_label)
        self.main_layout.add_widget(playlist_layout)
        
        theme_layout = BoxLayout(size_hint=(1, 0.08), spacing=10)
        self.theme_label = Label(text='Theme:', size_hint=(0.3, 1))
        self.theme_spinner = Spinner(
            text=self.store.get('theme')['name'] if self.store.exists('theme') else 'Dark Knight',
            values=list(self.themes.keys()),
            size_hint=(0.7, 1)
        )
        self.theme_spinner.bind(text=self.on_theme_change)
        theme_layout.add_widget(self.theme_label)
        theme_layout.add_widget(self.theme_spinner)
        self.main_layout.add_widget(theme_layout)

        self.output_dir = self.get_default_download_dir()
        self.folder_button = Button(text=f'Output: {os.path.basename(self.output_dir)}', size_hint=(1, 0.08))
        self.folder_button.bind(on_press=self.choose_folder)
        self.main_layout.add_widget(self.folder_button)
        
        buttons_layout = BoxLayout(size_hint=(1, 0.08), spacing=10)
        self.download_button = Button(text='Download')
        self.download_button.bind(on_press=self.start_download)
        self.stop_button = Button(text='Stop', disabled=True)
        self.stop_button.bind(on_press=self.stop_download)
        self.clear_button = Button(text='Clear')
        self.clear_button.bind(on_press=self.clear_fields)
        buttons_layout.add_widget(self.download_button)
        buttons_layout.add_widget(self.stop_button)
        buttons_layout.add_widget(self.clear_button)
        self.main_layout.add_widget(buttons_layout)
        
        self.progress_bar = ProgressBar(max=100, size_hint=(1, 0.05))
        self.main_layout.add_widget(self.progress_bar)
        
        self.status_label = Label(text='Ready', size_hint=(1, 0.1))
        self.main_layout.add_widget(self.status_label)
        
        self.is_downloading = False
        self.apply_theme(self.theme_spinner.text)
        
        return self.main_layout
    
    def on_theme_change(self, spinner, text):
        self.apply_theme(text)
        self.store.put('theme', name=text)

    def apply_theme(self, theme_name):
        theme = self.themes.get(theme_name, self.themes['Dark Knight'])
        self.bg_color.rgba = theme['bg']
        
        widgets_to_theme = [self.playlist_label, self.theme_label, self.status_label]
        for widget in widgets_to_theme:
            widget.color = theme['text']

        self.url_input.background_color = theme['input_bg']
        self.url_input.foreground_color = theme['text']

        self.theme_spinner.background_color = theme['button_bg']
        self.folder_button.background_color = theme['button_bg']
        self.stop_button.background_color = get_color_from_hex('#D93939')
        self.clear_button.background_color = theme['button_bg']
        self.download_button.background_color = theme['primary_button_bg']

    def _update_background(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def get_default_download_dir(self):
        if platform == 'android':
            from android.storage import primary_external_storage_path
            return os.path.join(primary_external_storage_path(), 'Download')
        else:
            return os.path.expanduser('~/Downloads')
    
    def choose_folder(self, instance):
        content = BoxLayout(orientation='vertical')
        filechooser = FileChooserListView(path=self.output_dir, dirselect=True, size_hint=(1, 0.9))
        content.add_widget(filechooser)
        buttons = BoxLayout(size_hint=(1, 0.1))
        select_btn = Button(text='Select')
        cancel_btn = Button(text='Cancel')
        buttons.add_widget(select_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)
        popup = Popup(title='Choose Output Folder', content=content, size_hint=(0.9, 0.9))
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
        
        thread = threading.Thread(target=self.download_thread, args=(urls,))
        thread.daemon = True
        thread.start()
    
    def stop_download(self, instance):
        self.is_downloading = False
    
    def download_thread(self, urls):
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = DummyStream()
        sys.stderr = DummyStream()
        
        try:
            url_list = [url.strip() for url in urls.split('\n') if url.strip()]
            total_urls = len(url_list)

            for i, url in enumerate(url_list, 1):
                if not self.is_downloading: break

                # --- FINÁLNA OPRAVA POČÍTADLA ---
                def my_hook(d):
                    if not self.is_downloading: raise yt_dlp.utils.DownloadCancelled()
                    if d['status'] == 'downloading':
                        # Zistíme, či sťahujeme playlist a podľa toho zostavíme text
                        playlist_index = d.get('playlist_index')
                        playlist_count = d.get('playlist_count')
                        
                        if playlist_index and playlist_count:
                            status_prefix = f'Downloading playlist ({playlist_index}/{playlist_count})... '
                        else:
                            # Pre samostatné linky použijeme počítadlo z vonkajšieho cyklu
                            status_prefix = f'Downloading ({i}/{total_urls})... '

                        p_str = d.get('_percent_str', '0.0%').replace('%', '').strip()
                        try:
                            p = float(p_str)
                            final_status_text = f"{status_prefix}{p:.1f}%"
                            Clock.schedule_once(lambda dt, prog=p: setattr(self.progress_bar, 'value', prog))
                            Clock.schedule_once(lambda dt, text=final_status_text: setattr(self.status_label, 'text', text))
                        except ValueError: pass
                    elif d['status'] == 'finished':
                        Clock.schedule_once(lambda dt: setattr(self.progress_bar, 'value', 100))

                output_path = os.path.join(self.output_dir, '%(title)s.%(ext)s')
                
                # Vraciame sa k jednoduchej a stabilnej logike pre playlisty
                ydl_opts = {
                    'outtmpl': output_path,
                    'progress_hooks': [my_hook],
                    'noplaylist': not self.playlist_check.active,
                    'playlist_items': '1' if not self.playlist_check.active else None,
                    'format': 'bestaudio[ext=m4a]/bestaudio/best',
                    'ignoreerrors': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

            if self.is_downloading:
                Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 'All downloads complete!'))
        
        except yt_dlp.utils.DownloadCancelled:
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 'Download stopped'))
        except Exception as e:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            Clock.schedule_once(lambda dt, err=str(e): self.show_error(f"Error: {err}"))
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            Clock.schedule_once(lambda dt: self.download_finished())

    def download_finished(self, *args):
        if self.is_downloading:
             if 'Error' not in self.status_label.text:
                self.status_label.text = 'Finished'
        
        self.is_downloading = False
        self.download_button.disabled = False
        self.stop_button.disabled = True
    
    def show_error(self, message):
        self.status_label.text = 'Error'
        error_label = Label(text=message, size_hint_y=None, valign='top')
        error_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        scroll_view = ScrollView(size_hint_y=None, height=Window.height * 0.3)
        scroll_view.add_widget(error_label)
        popup = Popup(title='Error', content=scroll_view, size_hint=(0.9, 0.5))
        popup.open()

    def on_pause(self): return True
    def on_resume(self): pass

if __name__ == '__main__':
    AudioXtractorApp().run()
