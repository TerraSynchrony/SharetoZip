"""
SharetoZip - Android Share-to MVP
Receives shared files via Android intent and compresses them into a .zip file.
"""

import os
import zipfile
from datetime import datetime
from functools import wraps

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView


# No-op fallback; on Android this is replaced with the real UI-thread dispatcher.
def run_on_ui_thread(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


try:
    from android import activity
    from android.runnable import run_on_ui_thread
    from jnius import autoclass

    Intent = autoclass("android.content.Intent")
    Uri = autoclass("android.net.Uri")
    ANDROID = True
except ImportError:
    ANDROID = False


def get_shared_uris(intent):
    """Extract URIs from an Android share intent (single or multiple files)."""
    uris = []
    if not ANDROID or intent is None:
        return uris

    action = intent.getAction()
    if action == "android.intent.action.SEND":
        uri = intent.getParcelableExtra(Intent.EXTRA_STREAM)
        if uri:
            uris.append(uri)
    elif action == "android.intent.action.SEND_MULTIPLE":
        stream_list = intent.getParcelableArrayListExtra(Intent.EXTRA_STREAM)
        if stream_list:
            for uri in stream_list.toArray():
                if uri:
                    uris.append(uri)

    return uris


def resolve_uri_to_path(context, uri):
    """Resolve a content URI to a real filesystem path."""
    try:
        cursor = context.getContentResolver().query(uri, None, None, None, None)
        if cursor and cursor.moveToFirst():
            idx = cursor.getColumnIndex("_data")
            if idx >= 0:
                path = cursor.getString(idx)
                cursor.close()
                if path:
                    return path
        if cursor:
            cursor.close()
    except Exception:
        pass

    # Fallback: read raw bytes from the content resolver
    return None


def stream_uri_to_zip(context, uri, zf, arcname):
    """Stream a content URI directly into an open ZipFile to avoid large in-memory buffers."""
    try:
        input_stream = context.getContentResolver().openInputStream(uri)
    except Exception as exc:
        raise IOError(f"Cannot open URI {uri}: {exc}") from exc
    try:
        buf = bytearray(65536)
        with zf.open(arcname, "w") as dest:
            while True:
                n = input_stream.read(buf, 0, len(buf))
                if n < 0:
                    break
                dest.write(bytes(buf[:n]))
    finally:
        input_stream.close()


def get_filename_from_uri(context, uri):
    """Derive a filename from the URI's last path segment or display name."""
    try:
        cursor = context.getContentResolver().query(uri, None, None, None, None)
        if cursor and cursor.moveToFirst():
            idx = cursor.getColumnIndex("_display_name")
            if idx >= 0:
                name = cursor.getString(idx)
                cursor.close()
                if name:
                    return name
        if cursor:
            cursor.close()
    except Exception:
        pass
    last = uri.getLastPathSegment()
    return last if last else "shared_file"


def build_zip(context, uris):
    """
    Build a zip archive from the provided URIs.
    Returns the path to the created zip file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = context.getExternalFilesDir(None).getAbsolutePath() if ANDROID else "/tmp"
    zip_path = os.path.join(output_dir, f"shared_{timestamp}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for uri in uris:
            filename = get_filename_from_uri(context, uri) if ANDROID else str(uri)
            path = resolve_uri_to_path(context, uri) if ANDROID else str(uri)
            if path and os.path.exists(path):
                zf.write(path, arcname=os.path.basename(path))
            elif ANDROID:
                stream_uri_to_zip(context, uri, zf, filename)

    return zip_path


class ShareToZipApp(App):
    """Main Kivy application."""

    def build(self):
        self.title = "SharetoZip"
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        self.status_label = Label(
            text="Waiting for shared files...",
            size_hint=(1, None),
            height=60,
            halign="center",
        )
        self.status_label.bind(size=self.status_label.setter("text_size"))

        scroll = ScrollView(size_hint=(1, 1))
        self.file_list_label = Label(
            text="",
            size_hint_y=None,
            halign="left",
            valign="top",
        )
        self.file_list_label.bind(
            texture_size=lambda instance, value: setattr(instance, "height", value[1])
        )
        scroll.add_widget(self.file_list_label)

        self.zip_button = Button(
            text="Create ZIP",
            size_hint=(1, None),
            height=50,
            disabled=True,
        )
        self.zip_button.bind(on_press=self.create_zip)

        self.layout.add_widget(self.status_label)
        self.layout.add_widget(scroll)
        self.layout.add_widget(self.zip_button)

        self._pending_uris = []

        if ANDROID:
            activity.bind(on_new_intent=self.on_new_intent)
            self.handle_intent(activity.getIntent())

        return self.layout

    @run_on_ui_thread
    def on_new_intent(self, intent):
        self.handle_intent(intent)

    def handle_intent(self, intent):
        """Process an incoming Android intent."""
        uris = get_shared_uris(intent)
        if uris:
            self._pending_uris = uris
            names = []
            for uri in uris:
                if ANDROID:
                    context = activity.getApplicationContext()
                    names.append(get_filename_from_uri(context, uri))
                else:
                    names.append(str(uri))
            self.file_list_label.text = "\n".join(f"• {n}" for n in names)
            self.status_label.text = f"{len(uris)} file(s) ready to zip."
            self.zip_button.disabled = False
        else:
            self.status_label.text = "No files received. Use 'Share to' from another app."

    def create_zip(self, _instance):
        """Compress pending files and report the result."""
        if not self._pending_uris:
            self.status_label.text = "No files to zip."
            return
        try:
            if ANDROID:
                context = activity.getApplicationContext()
            else:
                context = None
            zip_path = build_zip(context, self._pending_uris)
            self.status_label.text = f"ZIP created:\n{zip_path}"
            self.zip_button.disabled = True
            self._pending_uris = []
        except Exception as exc:
            self.status_label.text = f"Error: {exc}"


if __name__ == "__main__":
    ShareToZipApp().run()
