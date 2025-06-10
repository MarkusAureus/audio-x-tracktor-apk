[app]

# (required) Title of your application
title = Audio X-tracktor

# (required) Package name
package.name = audioxtracktor

# (required) Package domain (usually follows reverse domain name notation)
package.domain = com.markusaureus

# (required) Source code where the main.py lives
source.dir = .

# (required) Name of the main py file
source.main_py = main.py

# (optional) Filename to be used for the icon of the application.
icon.filename = %(source.dir)s/icon-512x512.png

# (optional) Presplash of the application.
presplash.filename = %(source.dir)s/presplash_screen.png

# (required) Version of your application
version = 3.0

# (required) List of requirements
requirements = python3,kivy,yt-dlp,pyjnius,android

# (optional) Application orientation
orientation = portrait

# (optional) Make the application fullscreen.
fullscreen = 0

# (optional) List of Android permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, FOREGROUND_SERVICE


[buildozer]

# (int) Log level (0 = error, 1 = info, 2 = debug (very verbose))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) The directory in which python-for-android will be cloned
p4a.branch = master

# (str) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (int) Android API to use
android.api = 31

# (int) Minimum API required
android.minapi = 21
