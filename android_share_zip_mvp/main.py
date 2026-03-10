from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.utils import platform

import os
import time
import shutil
import zipfile
from pathlib import Path


class ShareZipApp(App):
    def build(self):
        self.title = "Share to Zip"
        root = BoxLayout(orientation="vertical", padding=16, spacing=12)
        self.status = Label(
            text="Waiting for shared files...\nOpen Android Share and pick this app.",
            halign="left",
            valign="top",
            text_size=(0, None),
        )
        self.log = TextInput(readonly=True, multiline=True)
        retry = Button(text="Re-read share intent", size_hint=(1, None), height=56)
        retry.bind(on_release=lambda *_: self.process_share_intent())
        root.add_widget(self.status)
        root.add_widget(retry)
        root.add_widget(self.log)
        Clock.schedule_once(lambda *_: self.process_share_intent(), 0.5)
        return root

    def set_status(self, message: str):
        self.status.text = message
        self.append_log(message)

    def append_log(self, message: str):
        if self.log.text:
            self.log.text += "\n" + message
        else:
            self.log.text = message

    def process_share_intent(self):
        if platform != "android":
            self.set_status("This MVP only handles Android share intents on device.")
            return

        try:
            uris = get_shared_uris()
            if not uris:
                self.set_status("No shared files found in the current Android intent.")
                return

            out_path, count = zip_shared_uris_to_downloads(uris)
            self.set_status(f"Created ZIP with {count} file(s):\n{out_path}")
        except Exception as exc:
            self.set_status(f"Error: {exc}")


def get_shared_uris():
    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Intent = autoclass("android.content.Intent")
    activity = PythonActivity.mActivity
    intent = activity.getIntent()
    action = intent.getAction()
    uris = []

    if action == Intent.ACTION_SEND:
        stream = intent.getParcelableExtra(Intent.EXTRA_STREAM)
        if stream is not None:
            uris.append(stream)
    elif action == Intent.ACTION_SEND_MULTIPLE:
        parcelable_list = intent.getParcelableArrayListExtra(Intent.EXTRA_STREAM)
        if parcelable_list is not None:
            for i in range(parcelable_list.size()):
                uris.append(parcelable_list.get(i))

    return uris


def guess_display_name(content_resolver, uri):
    from jnius import autoclass

    OpenableColumns = autoclass("android.provider.OpenableColumns")
    name = None
    cursor = content_resolver.query(uri, None, None, None, None)
    if cursor is not None:
        try:
            if cursor.moveToFirst():
                idx = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if idx >= 0:
                    name = cursor.getString(idx)
        finally:
            cursor.close()
    if not name:
        name = f"shared_{int(time.time() * 1000)}"
    return sanitize_filename(name)


def sanitize_filename(name: str) -> str:
    keep = []
    for ch in name:
        if ch.isalnum() or ch in ("-", "_", ".", " "):
            keep.append(ch)
        else:
            keep.append("_")
    cleaned = "".join(keep).strip().strip(".")
    return cleaned or "shared_file"


def unique_name(target_dir: Path, original_name: str, used_names: set[str]) -> str:
    stem = Path(original_name).stem or "shared_file"
    suffix = Path(original_name).suffix
    candidate = original_name
    counter = 1
    while candidate in used_names or (target_dir / candidate).exists():
        candidate = f"{stem}_{counter}{suffix}"
        counter += 1
    used_names.add(candidate)
    return candidate


def copy_uri_to_cache(content_resolver, uri, target_path: str, chunk_size: int = 1024 * 1024):
    pfd = content_resolver.openFileDescriptor(uri, "r")
    if pfd is None:
        raise RuntimeError("Unable to open shared file descriptor")

    src_fd = os.dup(pfd.getFd())
    try:
        with os.fdopen(src_fd, "rb", closefd=True) as src, open(target_path, "wb") as out:
            shutil.copyfileobj(src, out, length=chunk_size)
    finally:
        pfd.close()


def create_zip_in_cache(file_paths, temp_dir: Path) -> Path:
    zip_path = temp_dir / f"shared_{time.strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in file_paths:
            zf.write(path, arcname=path.name)
    return zip_path


def publish_zip_to_downloads(local_zip_path: Path) -> str:
    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    MediaStore = autoclass("android.provider.MediaStore")
    MediaColumns = autoclass("android.provider.MediaStore$MediaColumns")
    ContentValues = autoclass("android.content.ContentValues")
    Environment = autoclass("android.os.Environment")

    activity = PythonActivity.mActivity
    resolver = activity.getContentResolver()

    values = ContentValues()
    values.put(MediaColumns.DISPLAY_NAME, local_zip_path.name)
    values.put(MediaColumns.MIME_TYPE, "application/zip")
    values.put(MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)

    collection = MediaStore.Downloads.EXTERNAL_CONTENT_URI
    item_uri = resolver.insert(collection, values)
    if item_uri is None:
        raise RuntimeError("Failed to create Downloads entry for ZIP")

    pfd = resolver.openFileDescriptor(item_uri, "w")
    if pfd is None:
        raise RuntimeError("Failed to open Downloads output descriptor")

    dst_fd = os.dup(pfd.getFd())
    try:
        with open(local_zip_path, "rb") as src, os.fdopen(dst_fd, "wb", closefd=True) as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
    finally:
        pfd.close()

    return f"Downloads/{local_zip_path.name}"


def zip_shared_uris_to_downloads(uris):
    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    activity = PythonActivity.mActivity
    resolver = activity.getContentResolver()

    cache_root = Path(activity.getCacheDir().getAbsolutePath()) / "incoming_share"
    if cache_root.exists():
        shutil.rmtree(cache_root)
    cache_root.mkdir(parents=True, exist_ok=True)

    incoming_dir = cache_root / "files"
    incoming_dir.mkdir(parents=True, exist_ok=True)

    used_names = set()
    file_paths = []
    for uri in uris:
        name = unique_name(incoming_dir, guess_display_name(resolver, uri), used_names)
        target = incoming_dir / name
        copy_uri_to_cache(resolver, uri, str(target))
        file_paths.append(target)

    temp_zip = create_zip_in_cache(file_paths, cache_root)
    published_path = publish_zip_to_downloads(temp_zip)
    return published_path, len(file_paths)


if __name__ == "__main__":
    ShareZipApp().run()
