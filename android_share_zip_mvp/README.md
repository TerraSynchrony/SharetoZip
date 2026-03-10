# SharetoZip – Android MVP

Lightweight Python app that appears in Android's **Share to** menu.  
Select any files or folders from a cloud storage app or your device, share them here, and get a neatly compressed `.zip` file saved to your device.

---

## Features

- Registers as a Share target for **any file type** (`*/*`)
- Accepts **single or multiple** files in one share action
- Creates a timestamped `.zip` using Python's built-in `zipfile` module
- Built with [Kivy](https://kivy.org/) and packaged with [Buildozer](https://buildozer.readthedocs.io/)

---

## Project structure

```
android_share_zip_mvp/
├── main.py              # Application entry point (Kivy + intent handling)
├── buildozer.spec       # Buildozer build configuration
├── intent_filters.xml   # Android intent-filter declarations
└── README.md            # This file
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| Buildozer | 1.5+ |
| Android SDK | API 33 |
| Android NDK | r25c or later |

Install Buildozer:

```bash
pip install buildozer
```

---

## Building the APK locally

```bash
cd android_share_zip_mvp
buildozer android debug
```

The resulting APK will be at `bin/sharetozip-0.1.0-arm64-v8a-debug.apk`.

To deploy directly to a connected device:

```bash
buildozer android debug deploy run
```

---

## Building via GitHub Actions

Push to `main` (or open a pull request) and the workflow defined in  
`.github/workflows/build-apk.yml` will automatically build the APK and upload it as an artifact.

---

## How it works

1. Another app (e.g. Files, Google Drive) triggers an `ACTION_SEND` or `ACTION_SEND_MULTIPLE` intent aimed at SharetoZip.
2. `main.py` receives the intent, resolves each URI to a filename, and lists them in the UI.
3. The user taps **Create ZIP** – the app reads each file through the content resolver and writes them into a single `.zip` archive in the app's external files directory.

---

## Permissions

| Permission | Reason |
|------------|--------|
| `READ_EXTERNAL_STORAGE` | Read files shared from external storage |
| `WRITE_EXTERNAL_STORAGE` | Save the resulting `.zip` to external storage |

---

## License

MIT
