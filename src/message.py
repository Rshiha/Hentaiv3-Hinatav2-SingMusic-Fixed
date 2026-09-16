"""
Message context: send/reply/photo/audio/video helpers for one incoming
message. Python port of Hinatav2's src/message.js, carrying over the original
Instagoat-render send_message / send_audio / send_video behavior (chunking
long text, muxing audio into a playable video for Instagram DMs, etc.)
unchanged.
"""

import os
import subprocess
import threading
import time
import urllib.parse

DOWNLOAD_DIR = "/tmp/downloads"

# Track message ids the bot itself has sent, so a reply to one of them can be
# treated as an AI follow-up (see events/on_message.py).
BOT_MSG_IDS = set()


def build_link(base_url, filename):
    return f"{base_url.rstrip('/')}/audio/{urllib.parse.quote(filename)}"


def make_playable_video(audio_path):
    """Mux a song onto a static color frame so it plays inline in Direct."""
    video_path = os.path.splitext(audio_path)[0] + ".mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=0x1DB954:s=720x720:r=1",
        "-i", audio_path,
        "-shortest",
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=100)
    if result.returncode != 0 or not os.path.isfile(video_path):
        print(f"FFMPEG ERR: {result.stderr[-500:]}", flush=True)
        return None
    return video_path


class MessageContext:
    """One of these is created per incoming DM. `send`/`reply` are the same
    thing for this transport (Instagram Direct has no true reply-to), kept as
    two names so command code can read naturally, same as Hinatav2's API."""

    def __init__(self, client, thread_id, ig_lock):
        self.client = client
        self.thread_id = thread_id
        self.ig_lock = ig_lock

    # ---- plain text / dict results -------------------------------------

    def _send_text(self, text):
        last_id = None
        for i in range(0, len(text), 1800):
            try:
                with self.ig_lock:
                    sent = self.client.direct_send(text[i:i + 1800], thread_ids=[self.thread_id])
                    last_id = getattr(sent, "id", None)
                time.sleep(0.5)
            except Exception as e:
                print(f"SEND ERR: {e}", flush=True)
        return last_id

    def send(self, result, remember=False):
        """Send a command result. Accepts a plain string, or a dict of the
        shape {"photo": url, "caption": ...} / {"type": "audio", ...} /
        {"type": "video", "path": ...}. Returns the sent message id."""
        if result is None:
            return None

        if isinstance(result, dict) and result.get("type") == "audio":
            return self.send_audio(result)
        if isinstance(result, dict) and result.get("type") == "video":
            return self.send_video(result.get("path"))
        if isinstance(result, dict) and result.get("photo"):
            return self._send_photo_dict(result)

        msg_id = self._send_text(str(result))
        if remember and msg_id:
            BOT_MSG_IDS.add(msg_id)
        return msg_id

    def reply(self, result):
        return self.send(result)

    def send_and_remember(self, result):
        """Send and remember the message id, so a reply to it can be routed
        back as an AI follow-up (mirrors original send_and_save)."""
        return self.send(result, remember=True)

    def _send_photo_dict(self, result):
        try:
            with self.ig_lock:
                self.client.direct_send_photo(result["photo"], thread_ids=[self.thread_id])
                msg_id = None
                if result.get("caption"):
                    sent = self.client.direct_send(result["caption"], thread_ids=[self.thread_id])
                    msg_id = getattr(sent, "id", None)
            return msg_id
        except Exception:
            return self._send_text(result.get("caption", "❌ Photo failed"))

    # ---- video -----------------------------------------------------------

    def send_video(self, path):
        if not path or not os.path.exists(path):
            self._send_text("❌ Video download failed!")
            return None
        try:
            if os.path.getsize(path) > 90 * 1024 * 1024:
                self._send_text("❌ Video 90MB-এর বেশি!")
                return None
            with self.ig_lock:
                self.client.direct_send_video(path, thread_ids=[self.thread_id])
        except Exception as e:
            print(f"VIDEO SEND ERR: {e}", flush=True)
            self._send_text("❌ Video send failed!")
        finally:
            try:
                os.remove(path)
            except Exception:
                pass
        return None

    # ---- audio (muxed into a playable video, same as the original) ------

    def send_audio(self, result):
        if not isinstance(result, dict):
            return self._send_text(result)

        path = result.get("path")
        if not path or not os.path.exists(path):
            self._send_text("❌ Audio file পাওয়া যায়নি!")
            return None

        video_path = None
        voice_path = None

        def do_cleanup():
            try:
                cleanup = result.get("cleanup")
                if cleanup:
                    cleanup()
                elif os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass
            try:
                if video_path and os.path.exists(video_path):
                    os.remove(video_path)
            except Exception:
                pass
            try:
                if voice_path and os.path.exists(voice_path):
                    os.remove(voice_path)
            except Exception:
                pass

        title = result.get("title", "Song")
        base_url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("BASE_URL")

        try:
            if os.path.getsize(path) > 90 * 1024 * 1024:
                self._send_text("❌ Audio 90MB-এর বেশি!")
                do_cleanup()
                return None

            # Current instagrapi exposes direct_send_voice(), which accepts
            # AAC audio in an MP4/M4A container. This is much closer to
            # Hinatav2's sendAudio/full-song flow than turning the song into
            # a fake video. If the installed client/account rejects voice
            # upload, fall back to the old playable-video method.
            sent_audio = False
            voice_path = os.path.splitext(path)[0] + "_voice.m4a"
            if hasattr(self.client, "direct_send_voice"):
                try:
                    subprocess.run([
                        "ffmpeg", "-y", "-i", path,
                        "-vn", "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", voice_path
                    ], capture_output=True, timeout=120, check=True)
                    if os.path.isfile(voice_path) and os.path.getsize(voice_path) <= 90 * 1024 * 1024:
                        print(f"🎵 Sending full audio: {title}", flush=True)
                        with self.ig_lock:
                            self.client.direct_send_voice(voice_path, thread_ids=[self.thread_id])
                        sent_audio = True
                        print("✅ FULL AUDIO SENT", flush=True)
                except Exception as e:
                    print(f"VOICE SEND ERR: {e}", flush=True)

            if not sent_audio:
                print(f"🎵 Falling back to playable video: {title}", flush=True)
                video_path = make_playable_video(path)
                if not video_path or os.path.getsize(video_path) > 90 * 1024 * 1024:
                    raise Exception("audio upload and video conversion both failed or too large")
                with self.ig_lock:
                    self.client.direct_send_video(video_path, thread_ids=[self.thread_id])
                print("✅ AUDIO SENT AS PLAYABLE VIDEO FALLBACK", flush=True)

            if base_url:
                audio_link = build_link(base_url, os.path.basename(path))
                self._send_text(
                    f"⬇️ Download ({title}) — 10 মিনিট valid:\n🎧 Audio: {audio_link}"
                )
                threading.Timer(600, do_cleanup).start()
            else:
                do_cleanup()
            return None

        except Exception as e:
            print(f"AUDIO SEND ERR: {e}", flush=True)
            try:
                if not base_url:
                    raise Exception("no base url for fallback link")
                link = build_link(base_url, os.path.basename(path))
                self._send_text(
                    f"🎵 {title}\n\n⚠️ Direct play fail করেছে, তাই link দিলাম (10 মিনিট valid):\n{link}"
                )
                threading.Timer(600, do_cleanup).start()
            except Exception as e2:
                print(f"AUDIO FALLBACK ERR: {e2}", flush=True)
                self._send_text("❌ গান পাঠানো যায়নি!")
                do_cleanup()
            return None
