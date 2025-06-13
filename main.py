# -----------------------------------------------------------------------------
# -- KIVY GUI FOR YT-DLP AUDIO DOWNLOADER                                    --
# -- Author: [Your Name/Nickname Here]                                       --
# -- Date: [Date of Creation]                                                --
# -- Version: 1.0                                                            --
# -----------------------------------------------------------------------------

# --- Standard Library Imports ---
import os
import sys
import threading
from urllib.parse import urlparse, parse_qsl

# --- Third-party Library Imports ---
import yt_dlp  # The core library for downloading video/audio

# --- Kivy Framework Imports ---
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

# Set a fixed window size for desktop platforms for a consistent mobile-like experience.
if platform not in ['android', 'ios']:
    Window.size = (400, 700)

class DummyStream:
    """
    A dummy stream class to suppress stdout/stderr output.
    This is used to prevent yt-dlp from printing directly to the console,
    allowing the GUI to handle all user feedback.
    """
    def write(self, *args, **kwargs):
        pass  # Absorb all write calls

    def flush(self, *args, **kwargs):
        pass  # Absorb all flush calls

class AudioXtractorApp(App):
    """
    The main application class for the Audio X-tracktor.
    It handles the GUI layout, event handling, and core application logic.
    """

    def build(self):
        """
        Initializes the application and builds the user interface.
        This method sets up all the widgets and their initial properties.
        """
        # Define color themes for the application's UI.
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
        # Use JsonStore to persist user settings (e.g., selected theme).
        self.store = JsonStore('settings.json')
        
        # --- Basic App Info ---
        self.title = 'Audio X-tracktor'
        self.icon = 'icon.png'
        
        # --- Main Layout ---
        # The root widget for the application.
        self.main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        # Bind the background update function to the layout's size and position.
        self.main_layout.bind(size=self._update_background)
        
        # --- Dynamic Background ---
        # Set up a colored rectangle as the background.
        with self.main_layout.canvas.before:
            self.bg_color = Color(0, 0, 0, 1)  # Initial color, will be updated by theme
            self.rect = Rectangle(size=self.main_layout.size, pos=self.main_layout.pos)
        
        # --- UI Widgets ---
        # Logo Image
        logo_image = Image(
            source='logo.png', size_hint=(1, 0.15),
            allow_stretch=True, keep_ratio=True
        )
        self.main_layout.add_widget(logo_image)
        
        # URL Input Field
        self.url_input = TextInput(
            hint_text='Enter URL(s) here...', multiline=True, size_hint=(1, 0.3)
        )
        self.main_layout.add_widget(self.url_input)
        
        # Playlist Download Option
        playlist_layout = BoxLayout(size_hint=(1, 0.08))
        self.playlist_check = CheckBox(size_hint=(0.1, 1))
        self.playlist_label = Label(text='Download entire playlist', size_hint=(0.9, 1))
        playlist_layout.add_widget(self.playlist_check)
        playlist_layout.add_widget(self.playlist_label)
        self.main_layout.add_widget(playlist_layout)
        
        # Theme Selector
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

        # Output Folder Selection Button
        self.output_dir = self.get_default_download_dir()
        self.folder_button = Button(text=f'Output: {os.path.basename(self.output_dir)}', size_hint=(1, 0.08))
        self.folder_button.bind(on_press=self.choose_folder)
        self.main_layout.add_widget(self.folder_button)
        
        # Action Buttons (Download, Stop, Clear)
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
        
        # Progress Bar
        self.progress_bar = ProgressBar(max=100, size_hint=(1, 0.05))
        self.main_layout.add_widget(self.progress_bar)
        
        # Status Label
        self.status_label = Label(text='Ready', size_hint=(1, 0.1))
        self.main_layout.add_widget(self.status_label)
        
        # --- Initial State ---
        self.is_downloading = False
        self.apply_theme(self.theme_spinner.text)  # Apply the stored or default theme
        
        return self.main_layout
    
    def on_theme_change(self, spinner, text):
        """
        Callback function for when a new theme is selected from the spinner.
        Applies the theme and saves the choice.
        """
        self.apply_theme(text)
        self.store.put('theme', name=text)

    def apply_theme(self, theme_name):
        """
        Applies the selected color theme to all relevant UI widgets.
        """
        theme = self.themes.get(theme_name, self.themes['Dark Knight'])
        self.bg_color.rgba = theme['bg']
        
        # Apply text color to labels
        for widget in [self.playlist_label, self.theme_label, self.status_label]:
            widget.color = theme['text']

        # Apply specific colors to inputs and buttons
        self.url_input.background_color = theme['input_bg']
        self.url_input.foreground_color = theme['text']
        self.theme_spinner.background_color = theme['button_bg']
        self.folder_button.background_color = theme['button_bg']
        self.stop_button.background_color = get_color_from_hex('#D93939') # Consistent stop color
        self.clear_button.background_color = theme['button_bg']
        self.download_button.background_color = theme['primary_button_bg']

    def _update_background(self, instance, value):
        """
        Updates the background rectangle's size and position when the window is resized.
        """
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def get_default_download_dir(self):
        """
        Determines the default download directory based on the operating system.
        """
        if platform == 'android':
            from android.storage import primary_external_storage_path
            return os.path.join(primary_external_storage_path(), 'Download')
        else:
            # For Windows, macOS, Linux
            return os.path.expanduser('~/Downloads')
    
    def choose_folder(self, instance):
        """
        Opens a popup with a file chooser to select the output directory.
        """
        content = BoxLayout(orientation='vertical')
        # 'dirselect=True' allows only directories to be selected.
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
            # Update the output directory if a selection was made.
            if filechooser.selection:
                self.output_dir = filechooser.selection[0]
                self.folder_button.text = f'Output: {os.path.basename(self.output_dir)}'
            popup.dismiss()
            
        select_btn.bind(on_press=on_select)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def clear_fields(self, instance):
        """
        Resets the URL input, progress bar, and status label to their initial state.
        """
        self.url_input.text = ''
        self.progress_bar.value = 0
        self.status_label.text = 'Ready'
    
    def start_download(self, instance):
        """
        Validates the input and starts the download process in a new thread.
        Using a separate thread prevents the GUI from freezing during the download.
        """
        urls = self.url_input.text.strip()
        if not urls:
            self.show_error('Please enter a URL')
            return
        
        # Update UI to reflect the downloading state
        self.is_downloading = True
        self.download_button.disabled = True
        self.stop_button.disabled = False
        self.status_label.text = 'Starting download...'
        
        # Run the download logic in a daemon thread
        thread = threading.Thread(target=self.download_thread, args=(urls,))
        thread.daemon = True
        thread.start()
    
    def stop_download(self, instance):
        """
        Sets a flag to gracefully stop the ongoing download process.
        The download_thread will check this flag and exit.
        """
        self.is_downloading = False
    
    def download_thread(self, urls):
        """
        The core download logic that runs in a separate thread.
        It configures and runs yt-dlp for each provided URL.
        """
        # Suppress yt-dlp's console output to avoid clutter and potential crashes.
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = DummyStream()
        sys.stderr = DummyStream()
        
        try:
            # Split URLs by newline for batch downloading.
            url_list = [url.strip() for url in urls.split('\n') if url.strip()]
            total_urls = len(url_list)

            # Iterate through each URL and download it.
            for i, url in enumerate(url_list, 1):
                if not self.is_downloading:
                    break # Exit if the user pressed the stop button.

                def my_hook(d):
                    """
                    A progress hook for yt-dlp. This function is called at different
                    stages of the download process (downloading, finished, error).
                    """
                    # Raise an exception to stop yt-dlp if the stop flag is set.
                    if not self.is_downloading:
                        raise yt_dlp.utils.DownloadCancelled()
                        
                    if d['status'] == 'downloading':
                        # Determine status text prefix for single videos vs playlists.
                        playlist_index = d.get('playlist_index')
                        playlist_count = d.get('playlist_count')
                        
                        if playlist_index and playlist_count:
                            status_prefix = f'Downloading playlist ({playlist_index}/{playlist_count})... '
                        else:
                            # Use the outer loop counter for individual links.
                            status_prefix = f'Downloading ({i}/{total_urls})... '

                        # Extract and parse the percentage string.
                        p_str = d.get('_percent_str', '0.0%').replace('%', '').strip()
                        try:
                            p = float(p_str)
                            final_status_text = f"{status_prefix}{p:.1f}%"
                            # Schedule UI updates on the main Kivy thread.
                            Clock.schedule_once(lambda dt, prog=p: setattr(self.progress_bar, 'value', prog))
                            Clock.schedule_once(lambda dt, text=final_status_text: setattr(self.status_label, 'text', text))
                        except ValueError:
                            pass # Ignore if percentage string is not a valid float.
                    elif d['status'] == 'finished':
                        # Set progress to 100% upon completion of a file.
                        Clock.schedule_once(lambda dt: setattr(self.progress_bar, 'value', 100))

                # Define the output filename template.
                output_path = os.path.join(self.output_dir, '%(title)s.%(ext)s')
                
                # yt-dlp options dictionary.
                ydl_opts = {
                    'outtmpl': output_path,
                    'progress_hooks': [my_hook],
                    # Download playlist if checked, otherwise only the single video from the URL.
                    'noplaylist': not self.playlist_check.active,
                    'playlist_items': '1' if not self.playlist_check.active else None,
                    # Request the best available audio, defaulting to m4a.
                    'format': 'bestaudio[ext=m4a]/bestaudio/best',
                    'ignoreerrors': True,  # Continue with the next video in case of an error.
                }
                
                # Create a YoutubeDL instance and start the download.
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

            # Final status update if the process was not cancelled.
            if self.is_downloading:
                Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 'All downloads complete!'))
        
        except yt_dlp.utils.DownloadCancelled:
            # This exception is raised by the hook when download is stopped.
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 'Download stopped'))
        except Exception as e:
            # Restore stdout/stderr to report the error properly.
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            print(f"An unexpected error occurred: {e}") # Log to console for debugging
            Clock.schedule_once(lambda dt, err=str(e): self.show_error(f"Error: {err}"))
        finally:
            # CRITICAL: Always restore original streams and reset UI state.
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            Clock.schedule_once(lambda dt: self.download_finished())

    def download_finished(self, *args):
        """
        Resets the UI to the 'ready' state after the download thread finishes.
        """
        # Set a final 'Finished' status if no error occurred.
        if self.is_downloading and 'Error' not in self.status_label.text:
            self.status_label.text = 'Finished'
        
        self.is_downloading = False
        self.download_button.disabled = False
        self.stop_button.disabled = True
    
    def show_error(self, message):
        """
        Displays an error message in a scrollable popup window.
        """
        self.status_label.text = 'Error'
        # Use a label inside a scroll view for long error messages.
        error_label = Label(text=message, size_hint_y=None, valign='top')
        error_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        scroll_view = ScrollView(size_hint_y=None, height=Window.height * 0.3)
        scroll_view.add_widget(error_label)
        
        popup = Popup(title='Error', content=scroll_view, size_hint=(0.9, 0.5))
        popup.open()

    # --- Kivy App Lifecycle Methods ---
    def on_pause(self):
        """
        Required for mobile apps; returning True allows the app to be paused.
        """
        return True

    def on_resume(self):
        """
        Called when the app is resumed from a paused state.
        """
        pass

# --- Application Entry Point ---
if __name__ == '__main__':
    AudioXtractorApp().run()
