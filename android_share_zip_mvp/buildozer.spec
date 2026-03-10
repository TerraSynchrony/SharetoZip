[app]

# Application metadata
title           = SharetoZip
package.name    = sharetozip
package.domain  = org.sharetozip

# Source
source.dir      = .
source.include_exts = py,png,jpg,kv,atlas,xml

# Application version
version         = 0.1.0

# Requirements – kivy + android bindings
requirements    = python3,kivy,pyjnius,android

# Android manifest extras
android.manifest.intent_filters = intent_filters.xml

# Permissions required to read shared files
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# Target / minimum Android API levels
android.api     = 33
android.minapi  = 21
android.ndk_api = 21

# Architecture(s) to build for (arm64 covers most modern devices)
android.archs   = arm64-v8a

# Enable AndroidX
android.enable_androidx = True

# Entry point
entrypoint      = main.py

[buildozer]

# Buildozer log level (0 = error, 1 = info, 2 = debug)
log_level = 2

# Warn before building for target that has not been tested
warn_on_root = 1
