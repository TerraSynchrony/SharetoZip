# ShareToZip MVP

A lightweight Python MVP for Android that appears in the system Share sheet, accepts one or many files of any type, and creates a ZIP archive directly in **Downloads**.

## Stack
- Python
- Kivy
- pyjnius
- Buildozer

## What it does
- Registers as a share target for `*/*`
- Handles both `ACTION_SEND` and `ACTION_SEND_MULTIPLE`
- Reads Android `content://` URIs through `ContentResolver`
- Copies shared files into app cache
- Builds a compressed ZIP
- Publishes the ZIP into the public **Downloads** collection using `MediaStore`

## Why this Downloads approach works
Instead of writing to a raw filesystem path, this MVP inserts the ZIP into Android's Downloads provider with `MediaStore.Downloads.EXTERNAL_CONTENT_URI`. That keeps it compatible with modern Android scoped storage on API 29+.

## Fast local build

```bash
pip install buildozer cython
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses-dev libtinfo6 cmake libffi-dev libssl-dev
buildozer android debug
```

APK output is typically under:

```bash
bin/sharetozip-0.1-arm64-v8a-debug.apk
```

## Rapid deploy options
1. Sideload the APK directly with `adb install -r <apk>`.
2. Use GitHub Actions to build on push.
3. For a no-store MVP, distribute the debug APK internally.

## Expected output
After sharing files into the app, the ZIP will appear as something like:

```
Downloads/shared_20260310_181500.zip
```

## Notes
- No special storage permission is needed for writing into Downloads through `MediaStore` on modern Android.
- Shared URI access is temporary and granted by Android at share time.
- Duplicate source filenames are automatically de-conflicted inside the archive.
- This version uses buffered file descriptor copies, so it is substantially better for large files than the earlier byte-by-byte MVP.
