[app]
title = ShareToZip
package.name = sharetozip
package.domain = com.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt
version = 0.1
requirements = python3,kivy,pyjnius
orientation = portrait
fullscreen = 0
android.api = 34
android.minapi = 26
android.archs = arm64-v8a, armeabi-v7a
android.permissions = INTERNET
android.allow_backup = True

# Android share targets for any file type
android.manifest.intent_filters = intent_filters.xml

[buildozer]
log_level = 2
warn_on_root = 1
