import os
import time
import glob
import uuid
import shutil
import requests
import yt_dlp

DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

PENDING_SEARCH = {}

JIOSAAVN_API = os.getenv(
    "JIOSAAVN_API",
    "https://jiosaavn-api-dnpu.onrender.com/api/search/songs"
)
JIO_DIRECT_API = "https://www.jiosaavn.com/api.php"


# =========================================================
# JIOSAAVN SEARCH (PRIMARY)
# =========================================================

def _jio_direct_search(song_name, limit=10):
    """Direct JioSaavn web API fallback.

    This avoids depending on one third-party Render proxy. The web API
    exposes search results; when a direct media URL is present we keep it as
    a playable full-song candidate. See the current JioSaavn API reverse-
    engineering documentation for the search.getResults endpoint.
    """
    params = {
        "__call": "search.getResults",
        "q": song_name,
        "n": limit,
        "p": 1,
        "_format": "json",
        "_marker": 0,
        "ctx": "web6dot0",
        "api_version": 4,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/139 Safari/537.36",
        "Accept": "application/json,text/plain,*/*",
        "Referer": "https://www.jiosaavn.com/",
    }
    r = requests.get(JIO_DIRECT_API, params=params, headers=headers, timeout=12)
    r.raise_for_status()
    data = r.json()
    songs = (data.get("results") or data.get("data", {}).get("results") or [])
    results = []
    for song in songs:
        if not isinstance(song, dict):
            continue
        more = song.get("more_info") or {}
        media_url = (
            song.get("media_url")
            or song.get("url")
            or more.get("media_url")
            or more.get("encrypted_media_url")
        )
        # encrypted_media_url cannot be downloaded directly without the
        # service's decryption routine, so only accept actual HTTP media URLs.
        if not isinstance(media_url, str) or not media_url.startswith("http"):
            continue
        artist = song.get("subtitle") or song.get("artist") or "Unknown"
        if isinstance(artist, dict):
            artist = artist.get("name") or "Unknown"
        results.append({
            "source": "jiosaavn",
            "title": song.get("title") or song.get("song") or song.get("name") or "Unknown",
            "artist": artist,
            "duration": song.get("duration") or more.get("duration") or 0,
            "download_url": media_url,
        })
    return results


def get_jiosaavn_results(song_name, limit=10):
    """Search JioSaavn through two independent endpoints."""
    results = []

    # 1) Existing proxy, kept as the fast path when it is healthy.
    for attempt in range(2):
        try:
            response = requests.get(
                JIOSAAVN_API,
                params={"query": song_name, "limit": limit},
                headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
                timeout=12,
            )
            response.raise_for_status()
            data = response.json()
            songs = data.get("data", {}).get("results", [])
            for song in songs:
                if not isinstance(song, dict):
                    continue
                links = song.get("downloadUrl") or []
                best_url = None
                if isinstance(links, list):
                    for link in reversed(links):
                        if isinstance(link, dict):
                            best_url = link.get("url") or link.get("link")
                            if best_url:
                                break
                if not best_url:
                    best_url = song.get("media_url") or song.get("url")
                if best_url:
                    results.append({
                        "source": "jiosaavn",
                        "title": song.get("name") or song.get("title") or "Unknown",
                        "artist": song.get("primaryArtists") or song.get("artist") or "Unknown",
                        "duration": song.get("duration") or 0,
                        "download_url": best_url,
                    })
            if results:
                break
        except Exception as e:
            print(f"JIOSAAVN PROXY ERR (attempt {attempt + 1}): {e}", flush=True)
            if attempt == 0:
                time.sleep(1)

    # 2) Direct JioSaavn search fallback.
    if len(results) < limit:
        try:
            direct = _jio_direct_search(song_name, limit=limit)
            seen = {str(x.get("download_url")) for x in results}
            for item in direct:
                if str(item.get("download_url")) not in seen:
                    results.append(item)
                    seen.add(str(item.get("download_url")))
        except Exception as e:
            print(f"JIOSAAVN DIRECT SEARCH ERR: {e}", flush=True)

    return results[:limit]


# =========================================================
# DOWNLOAD JIOSAAVN SONG
# =========================================================

def download_jiosaavn_song(
    download_url,
    title
):

    job_id = uuid.uuid4().hex

    path = os.path.join(
        DOWNLOAD_DIR,
        f"{job_id}.m4a"
    )

    try:

        print(
            f"🎵 Downloading (JioSaavn): {title}",
            flush=True
        )

        response = requests.get(
            download_url,
            stream=True,
            timeout=30
        )

        response.raise_for_status()

        with open(path, "wb") as f:

            for chunk in response.iter_content(
                chunk_size=1024 * 64
            ):

                if chunk:
                    f.write(chunk)

        if not os.path.isfile(path):
            return None, None

        print(
            f"✅ AUDIO READY: {path}",
            flush=True
        )

        return path, title

    except Exception as e:

        print(
            f"JIOSAAVN DOWNLOAD ERR: {e}",
            flush=True
        )

        return None, None


# =========================================================
# COOKIES
# =========================================================

def find_cookie_file():
    paths = [
        os.getenv("YTDLP_COOKIES"),
        "/etc/secrets/cookies.txt",
        "cookies.txt",
        os.path.join(os.getcwd(), "cookies.txt"),
    ]

    for path in paths:
        if not path:
            continue

        try:
            if os.path.isfile(path):
                if os.path.getsize(path) <= 0:
                    continue

                if path.startswith("/etc/secrets"):
                    tmp_path = "/tmp/cookies.txt"

                    try:
                        shutil.copyfile(
                            path,
                            tmp_path
                        )
                        return tmp_path
                    except Exception:
                        return path

                return path

        except Exception:
            continue

    return None


# =========================================================
# YOUTUBE SEARCH
# =========================================================

def get_youtube_search_results(song_name, limit=5):

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "noplaylist": True,
    }

    cookie_file = find_cookie_file()

    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file

    try:
        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:

            info = ydl.extract_info(
                f"ytsearch{limit}:{song_name}",
                download=False
            )

            entries = info.get(
                "entries",
                []
            )

            results = []

            for entry in entries:
                if not entry:
                    continue

                video_id = entry.get("id")
                title = entry.get(
                    "title",
                    "Unknown"
                )

                if not video_id:
                    continue

                results.append({
                    "id": video_id,
                    "title": title
                })

            return results

    except Exception as e:

        print(
            f"SEARCH ERROR: {e}",
            flush=True
        )

        return []


# =========================================================
# DOWNLOAD AUDIO
# =========================================================

def get_youtube_audio_by_url(
    video_id,
    video_title
):

    job_id = uuid.uuid4().hex

    output_template = os.path.join(
        DOWNLOAD_DIR,
        f"{job_id}.%(ext)s"
    )

    ydl_opts = {
        "format": (
            "bestaudio[ext=m4a]"
            "/bestaudio"
            "/best"
        ),

        "outtmpl": output_template,

        "noplaylist": True,

        "quiet": True,
        "no_warnings": True,

        "retries": 5,

        "fragment_retries": 5,

        "socket_timeout": 30,

        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/139.0.0.0 "
                "Safari/537.36"
            )
        },

        "extractor_args": {
            "youtube": {
                "player_client": [
                    "android",
                    "ios",
                    "web"
                ]
            }
        },

        "ignoreerrors": False
    }

    cookie_file = find_cookie_file()

    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file

        print(
            f"🍪 Music cookies: {cookie_file}",
            flush=True
        )

    url = (
        "https://www.youtube.com/watch?v="
        + str(video_id)
    )

    try:

        print(
            f"🎵 Downloading: {video_title}",
            flush=True
        )

        fallback_clients = [
            ["android"],
            ["android", "web"],
            ["ios"],
            ["mweb"],
            ["tv_embedded"],
        ]

        try:
            with yt_dlp.YoutubeDL(
                ydl_opts
            ) as ydl:

                ydl.extract_info(
                    url,
                    download=True
                )

        except Exception as first_err:

            if "not available" not in str(first_err) and \
               "reloaded" not in str(first_err):
                raise

            last_err = first_err

            for clients in fallback_clients:

                print(
                    f"⚠️ Format fallback: trying {clients}",
                    flush=True
                )

                retry_opts = dict(ydl_opts)
                retry_opts["format"] = "best"
                retry_opts["extractor_args"] = {
                    "youtube": {
                        "player_client": clients
                    }
                }

                try:
                    with yt_dlp.YoutubeDL(
                        retry_opts
                    ) as ydl:

                        ydl.extract_info(
                            url,
                            download=True
                        )

                    last_err = None
                    break

                except Exception as retry_err:
                    last_err = retry_err
                    continue

            # সব নির্দিষ্ট client fail করলে, একদম শেষ চেষ্টা হিসেবে
            # কোনো player_client restriction ছাড়াই সবচেয়ে permissive
            # format দিয়ে try করা — yt-dlp নিজে যেটা পাচ্ছে সেটাই নেবে।
            if last_err:

                print(
                    "⚠️ Format fallback: trying unrestricted (any client)",
                    flush=True
                )

                retry_opts = dict(ydl_opts)
                retry_opts["format"] = "worst"
                retry_opts.pop("extractor_args", None)

                try:
                    with yt_dlp.YoutubeDL(
                        retry_opts
                    ) as ydl:

                        ydl.extract_info(
                            url,
                            download=True
                        )

                    last_err = None

                except Exception as retry_err:
                    last_err = retry_err

            if last_err:
                raise last_err

        files = glob.glob(
            os.path.join(
                DOWNLOAD_DIR,
                f"{job_id}.*"
            )
        )

        files = [
            f for f in files
            if os.path.isfile(f)
        ]

        if not files:
            print(
                "❌ Audio file পাওয়া যায়নি",
                flush=True
            )

            return None, None

        path = files[0]

        print(
            f"✅ AUDIO READY: {path}",
            flush=True
        )

        return path, video_title

    except Exception as e:

        print(
            f"AUDIO DOWNLOAD ERROR: {e}",
            flush=True
        )

        return None, None


# =========================================================
# PLAY / SONG / MUSIC
# =========================================================

def play(a, c):

    if isinstance(c, dict):
        user_id = str(
            c.get(
                "user_id",
                "default"
            )
        )
    else:
        user_id = str(
            c or "default"
        )

    if not a:
        return (
            "🎵 Usage:\n"
            ".play song name"
        )

    text = (
        " ".join(a)
        .strip()
    )

    # Number selection is handled separately
    # by select_song()
    if text.isdigit():
        return None

    results = get_jiosaavn_results(
        text,
        limit=10
    )

    # JioSaavn-এর ক্যাটালগ সীমিত (অনেক English/আঞ্চলিক/কম জনপ্রিয় গান
    # ওখানে নেই)। আগে শুধুমাত্র JioSaavn একদম খালি ফলাফল দিলে YouTube
    # চেক করা হতো — এখন JioSaavn-এ ৫টার কম রেজাল্ট পেলেও বাকিটা
    # YouTube দিয়ে পূরণ করা হচ্ছে, যাতে বেশিরভাগ গানই খুঁজে পাওয়া যায়।
    if len(results) < 10:

        needed = 10 - len(results)

        print(
            f"⚠️ JioSaavn এ মাত্র {len(results)}টা — "
            f"YouTube থেকে আরো {needed}টা আনা হচ্ছে",
            flush=True
        )

        yt_results = get_youtube_search_results(
            text,
            limit=needed
        )

        results += [
            {
                "source": "youtube",
                "title": r.get("title", "Unknown"),
                "video_id": r.get("id")
            }
            for r in yt_results
        ]

    if not results:
        return (
            "❌ কোনো গান পাওয়া যায়নি!"
        )

    PENDING_SEARCH[user_id] = results

    # Keep memory small
    if len(PENDING_SEARCH) > 50:

        first_key = next(
            iter(PENDING_SEARCH)
        )

        if first_key != user_id:
            PENDING_SEARCH.pop(
                first_key,
                None
            )

    def _duration(value):
        try:
            total = int(float(value or 0))
            return f"{total // 60}:{total % 60:02d}" if total > 0 else ""
        except Exception:
            return ""

    msg = f'🎵 Full songs for "{text}"\n\n'
    for i, result in enumerate(results, 1):
        title = str(result.get("title", "Unknown"))[:70]
        artist = str(result.get("artist", "") or "").strip()[:55]
        duration = _duration(result.get("duration"))
        details = f" — {artist}" if artist and artist.lower() != "unknown" else ""
        if duration:
            details += f" ({duration})"
        msg += f"{i}. {title}{details}\n"

    msg += f"\n👉 Song send করতে 1-{len(results)} এর মধ্যে একটি number পাঠাও।"

    return msg


# =========================================================
# SELECT SONG
# =========================================================

def select_song(number, c):

    if isinstance(c, dict):
        user_id = str(
            c.get(
                "user_id",
                "default"
            )
        )
    else:
        user_id = str(
            c or "default"
        )

    try:
        number = int(number)
    except Exception:
        return None

    results = PENDING_SEARCH.get(
        user_id
    )

    if not results:
        return (
            "❌ কোনো pending song নেই!\n"
            "আগে `.song গানের নাম` লিখো।"
        )

    index = number - 1

    if index < 0 or index >= len(results):
        return (
            f"❌ শুধু 1-{len(results)} এর মধ্যে "
            "একটা number দাও।"
        )

    selected = results[index]

    source = selected.get(
        "source",
        "youtube"
    )

    title = selected.get(
        "title",
        "Unknown"
    )

    # Remove pending result immediately
    # so repeated "1" does not download twice
    PENDING_SEARCH.pop(
        user_id,
        None
    )

    if source == "jiosaavn":

        download_url = selected.get(
            "download_url"
        )

        if not download_url:
            return (
                "❌ এই গানের link পাওয়া যায়নি!"
            )

        return {
            "type": "audio",
            "source": "jiosaavn",
            "download_url": download_url,
            "title": title
        }

    video_id = selected.get("video_id")

    if not video_id:
        return (
            "❌ এই গানটির YouTube ID পাওয়া যায়নি!"
        )

    return {
        "type": "audio",
        "source": "youtube",
        "video_id": video_id,
        "title": title
    }


# =========================================================
# DOWNLOAD SELECTED SONG
# =========================================================

def download_selected_song(
    result
):

    if not isinstance(
        result,
        dict
    ):
        return None

    if result.get("type") != "audio":
        return result

    source = result.get(
        "source",
        "youtube"
    )

    title = result.get(
        "title",
        "Unknown"
    )

    if source == "jiosaavn":

        download_url = result.get(
            "download_url"
        )

        if not download_url:
            return (
                "❌ Song link missing!"
            )

        path, real_title = (
            download_jiosaavn_song(
                download_url,
                title
            )
        )

    else:

        video_id = result.get(
            "video_id"
        )

        if not video_id:
            return (
                "❌ Song ID missing!"
            )

        path, real_title = (
            get_youtube_audio_by_url(
                video_id,
                title
            )
        )

    if not path:
        return (
            "❌ গান download করা যায়নি!"
        )

    return {
        "type": "audio",
        "path": path,
        "title": real_title or title,
        "cleanup": (
            lambda: safe_remove(path)
        )
    }


# =========================================================
# CLEANUP
# =========================================================

def safe_remove(path):

    if not path:
        return

    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


# =========================================================
# COMMANDS
# =========================================================

MEDIA_COMMANDS = {
    "play": play,
    "song": play,
    "music": play,
                            }

            
