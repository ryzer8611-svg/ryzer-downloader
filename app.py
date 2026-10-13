import os
import uuid
import subprocess
from pathlib import Path
from flask import Flask, render_template, request, send_file, abort, flash, redirect, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "work"
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "200"))
ALLOWED_EXTENSIONS = {"mp3", "wav", "m4a", "aac", "flac", "ogg", "mp4", "mov", "mkv", "webm", "avi", "mpeg", "mpg"}
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-before-production")
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.get("/")
def index():
    return render_template("index.html", max_upload_mb=MAX_UPLOAD_MB)


@app.post("/convert")
def convert():
    upload = request.files.get("media")
    output_format = request.form.get("format", "mp3").lower()
    if output_format not in {"mp3", "mp4"}:
        flash("Lütfen MP3 veya MP4 seç.", "error")
        return redirect(url_for("index"))
    if not upload or not upload.filename:
        flash("Önce bir dosya seç.", "error")
        return redirect(url_for("index"))
    if not allowed_file(upload.filename):
        flash("Bu dosya türü desteklenmiyor. MP3, WAV, M4A, MP4, MOV, MKV veya WEBM kullan.", "error")
        return redirect(url_for("index"))

    job_id = uuid.uuid4().hex
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=False)
    safe_name = secure_filename(upload.filename) or "media"
    source = job_dir / safe_name
    target = job_dir / f"converted.{output_format}"
    upload.save(source)

    # Converts user-uploaded files only; it does not fetch or download third-party URLs.
    command = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source)]
    if output_format == "mp3":
        command += ["-vn", "-codec:a", "libmp3lame", "-q:a", "2", str(target)]
    else:
        command += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-movflags", "+faststart", str(target)]

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=600, check=False)
    except subprocess.TimeoutExpired:
        flash("Dönüştürme zaman sınırını aştı. Daha küçük bir dosyayla tekrar dene.", "error")
        return redirect(url_for("index"))

    if result.returncode != 0 or not target.exists() or target.stat().st_size == 0:
        flash("Dosya dönüştürülemedi. Seçtiğin dosyanın sağlam ve desteklenen bir medya dosyası olduğundan emin ol.", "error")
        return redirect(url_for("index"))

    download_name = f"{Path(safe_name).stem}.{output_format}"
    return send_file(target, as_attachment=True, download_name=download_name, mimetype="audio/mpeg" if output_format == "mp3" else "video/mp4")


@app.errorhandler(413)
def too_large(_error):
    flash(f"Dosya çok büyük. En fazla {MAX_UPLOAD_MB} MB yükleyebilirsin.", "error")
    return redirect(url_for("index")), 413


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
