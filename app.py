"""くもりガラス（fog mirror）— Flask サーバー

役割はシンプルで、次の3つだけです。
  1. 画面（index.html）と JavaScript / CSS をブラウザに配る
  2. ブラウザで撮った写真を受け取って photos/ フォルダに保存する
  3. 保存した写真をギャラリー画面で一覧表示する

カメラ映像・手の検出・曇りの描画は、すべてブラウザ側（static/js/main.js）で動きます。
映像そのものはサーバーに送られません。送られるのは「写真に残す」を押した1枚だけです。
"""
from datetime import datetime
from pathlib import Path
import uuid

from flask import Flask, abort, jsonify, redirect, render_template, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
PHOTO_DIR = BASE_DIR / "photos"
PHOTO_DIR.mkdir(exist_ok=True)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024  # 1枚15MBまで


@app.get("/")
def index():
    return redirect("/fog")


@app.get("/fog")
def fog():
    # 貼ってもらった仕様どおりに作った1ファイル版（fog.html）
    return send_from_directory(BASE_DIR / "static", "fog.html")


@app.get("/gallery")
def gallery():
    photos = sorted(PHOTO_DIR.glob("*.png"), reverse=True)
    return render_template("gallery.html", photos=[p.name for p in photos])


@app.post("/api/photos")
def save_photo():
    data = request.get_data()
    if not data.startswith(PNG_SIGNATURE):
        return jsonify(error="PNG画像ではありません"), 400
    name = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6] + ".png"
    (PHOTO_DIR / name).write_bytes(data)
    return jsonify(name=name, url=f"/photos/{name}"), 201


@app.get("/photos/<path:name>")
def photo(name):
    if not name.endswith(".png"):
        abort(404)
    return send_from_directory(PHOTO_DIR, name)


if __name__ == "__main__":
    import sys

    # スマホから試すときは: python app.py --https
    # （カメラは https か localhost でしか使えないため。pyopenssl が必要）
    if "--https" in sys.argv:
        app.run(host="0.0.0.0", port=5000, ssl_context="adhoc", debug=True)
    else:
        app.run(host="127.0.0.1", port=5000, debug=True)
