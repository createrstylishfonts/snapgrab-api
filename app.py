from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import requests
import re

app = Flask(__name__)
CORS(app)

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Redmi A4 5G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
}

def extract_youtube_id(url):
    match = re.search(r'(?:v=|\/|youtu\.be\/|shorts\/)([0-9A-Za-z_-]{11})', url)
    return match.group(1) if match else None

def try_piped_youtube(video_id, fmt):
    piped_nodes = [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.tokhmi.xyz",
        "https://pipedapi.moomoo.me",
        "https://pipedapi.syncpundit.io"
    ]
    for node in piped_nodes:
        try:
            res = requests.get(f"{node}/streams/{video_id}", headers=HEADERS, timeout=10)
            if res.status_code == 200:
                data = res.json()
                title = data.get("title", "YouTube_Video")
                if fmt == "MP3":
                    audios = data.get("audioStreams", [])
                    if audios:
                        best_audio = sorted(audios, key=lambda x: x.get("bitrate", 0), reverse=True)[0]
                        return {"title": title, "download_url": best_audio["url"], "ext": "mp3"}
                else:
                    streams = [s for s in data.get("videoStreams", []) if not s.get("videoOnly") and s.get("mimeType", "").startswith("video/mp4")]
                    if streams:
                        best_vid = sorted(streams, key=lambda x: int(x.get("quality", "0").replace("p", "") or 0), reverse=True)[0]
                        return {"title": title, "download_url": best_vid["url"], "ext": "mp4"}
        except Exception:
            continue
    return None

def try_invidious_youtube(video_id, fmt):
    inv_nodes = [
        "https://inv.nadeko.net",
        "https://invidious.nerdvpn.de",
        "https://iv.ggtyler.dev"
    ]
    for node in inv_nodes:
        try:
            res = requests.get(f"{node}/api/v1/videos/{video_id}", headers=HEADERS, timeout=10)
            if res.status_code == 200:
                data = res.json()
                title = data.get("title", "YouTube_Video")
                if fmt == "MP3":
                    adaptive = [f for f in data.get("adaptiveFormats", []) if f.get("type", "").startswith("audio/")]
                    if adaptive:
                        return {"title": title, "download_url": adaptive[0]["url"], "ext": "mp3"}
                else:
                    formats = [f for f in data.get("formatStreams", []) if f.get("container") == "mp4"]
                    if formats:
                        return {"title": title, "download_url": formats[-1]["url"], "ext": "mp4"}
        except Exception:
            continue
    return None

def try_cobalt_youtube(url, fmt):
    cobalt_nodes = [
        "https://api.cobalt.tools/",
        "https://co.wuk.sh/api/json"
    ]
    payload = {
        "url": url,
        "downloadMode": "audio" if fmt == "MP3" else "auto",
        "videoQuality": "720",
        "audioFormat": "mp3"
    }
    for node in cobalt_nodes:
        try:
            res = requests.post(node, json=payload, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if data.get("url"):
                    return {
                        "title": data.get("filename", "YouTube_Video").rsplit('.', 1)[0],
                        "download_url": data["url"],
                        "ext": "mp3" if fmt == "MP3" else "mp4"
                    }
        except Exception:
            continue
    return None

@app.route('/')
def home():
    return "Snap Grab Multi-Engine API is Live!"

@app.route('/api/get-video', methods=['POST'])
def get_video():
    data = request.get_json()
    url = data.get('url')
    fmt = data.get('format', 'MP4')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    video_id = extract_youtube_id(url)
    is_youtube = ('youtube.com' in url or 'youtu.be' in url) and video_id

    if is_youtube:
        result = try_piped_youtube(video_id, fmt)
        if result:
            return jsonify(result)

        result = try_invidious_youtube(video_id, fmt)
        if result:
            return jsonify(result)

        result = try_cobalt_youtube(url, fmt)
        if result:
            return jsonify(result)

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 15,
        'retries': 1,
        'format': 'bestaudio/best' if fmt == 'MP3' else 'best[ext=mp4]/best'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'title': info.get('title', 'SnapGrab_Video'),
                'download_url': info.get('url'),
                'ext': 'mp3' if fmt == 'MP3' else info.get('ext', 'mp4')
            })
    except Exception as e:
        if is_youtube:
            return jsonify({'error': 'All YouTube nodes busy right now. Try another video or retry in 10s.'}), 500
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
                           
