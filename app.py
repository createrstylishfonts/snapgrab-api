from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

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

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestaudio/best' if fmt == 'MP3' else 'best[ext=mp4]/best',
        'extractor_args': {
            'youtube': {
                'player_client': ['tv', 'mweb', 'android']
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
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
    
