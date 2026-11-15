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

    # YouTube बायपास करने के लिए स्पेशल मोबाइल और वेब एजेंट्स (इन-बिल्ट)
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
        'retries': 2,
        'format': 'bestaudio/best' if fmt == 'MP3' else 'best[ext=mp4]/best',
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web', 'mweb'],
                'po_token': ['web+PO_TOKEN', 'mweb+PO_TOKEN']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate'
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
        # अगर फिर भी YouTube ब्लॉक करे, तो यूज़र को साफ़ मैसेज देने के लिए
        err_msg = str(e)
        if "sign in" in err_msg.lower() or "bot" in err_msg.lower() or "player" in err_msg.lower():
            return jsonify({'error': 'YouTube Temporary Block. Please try again or download Instagram/FB videos.'}), 500
        return jsonify({'error': err_msg}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
    
