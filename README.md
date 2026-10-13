# Ryzer Downloader / Media Converter

Mobil uyumlu Flask + FFmpeg web uygulaması. Kullanıcının yüklediği medya dosyalarını MP3 veya MP4'e dönüştürür.

## Render
- Runtime: Docker
- Dockerfile path: `./Dockerfile`
- No ZIP archive is required; the app files are copied directly into the image.
- Port: Render injects `PORT`; default is `10000`.

## Run locally
```bash
pip install -r requirements.txt
python app.py
```
FFmpeg must be installed on the host. For deployment, use the supplied Dockerfile.

This application converts uploaded files only and does not download third-party videos from YouTube URLs. Upload only content you own or have permission to process.
