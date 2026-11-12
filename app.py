from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import requests
import re

app = Flask(__name__)
CORS(app)

COBALT_INSTANCES = [
    "https://api.cobalt.tools",
    "https://cobalt-api.kwiatekmiki.com",
    "https://cobalt.api.timelessnesses.me"
]

def extract_youtube_id(url):
    match = re.search(r'(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})', url)
    return match.group(1) if match else None

def try_cobalt_youtube(url, fmt):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    payload = {
        "url": url,
        "downloadMode": "audio" if fmt == "MP3" else "auto",
        "videoQuality": "720",
        "audioFormat": "mp3"
    }
    for instance in COBALT_INSTANCES:
        try:
            res = requests.post(instance, json=payload, headers=headers, timeout=12)
            if res.status_code == 200:
                data = res.json()
                dl_url = data.get("url")
                if dl_url:
                    return {
                        "title": data.get("filename", "YouTube_Video").rsplit('.', 1)[0],
                        "download_url": dl_url,
                        "ext": "mp3" if fmt == "MP3" else "mp4"
                    }
        except Exception:
            continue
    return None

@app.route('/')
def home():
    return "Snap Grab API is Live!"

@app.route('/api/get-video', methods=['POST'])
def get_video():
    data = request.get_json()
    url = data.get('url')
    fmt = data.get('format', 'MP4')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    is_youtube = 'youtube.com' in url or 'youtu.be' in url

    # 1. यदि YouTube लिंक है तो पहले Cobalt से तेज़ कोशिश करें
    if is_youtube:
        cobalt_result = try_cobalt_youtube(url, fmt)
        if cobalt_result:
            return jsonify(cobalt_result)

    # 2. बाकी सभी साइट्स (Instagram, FB, X) और बैकअप के लिए yt-dlp
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 15,
        'retries': 1,
        'format': 'bestaudio/best' if fmt == 'MP3' else 'best[ext=mp4]/best',
        'extractor_args': {
            'youtube': {
                'player_client': ['tv', 'android']
            }
        }
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
            return jsonify({'error': 'YouTube server busy. Please try again in a moment.'}), 500
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
                
