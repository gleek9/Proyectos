import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Tuple
import yt_dlp
from config import settings

class MediaExtractor:
    def __init__(self):
        self.tmp_dir = settings.TMP_MEDIA_DIR
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def purge_all_tmp(self):
        """
        Purga todos los archivos temporales de audio o video restantes en tmp_media
        para garantizar 0 bytes de desperdicio de almacenamiento en disco.
        """
        try:
            if self.tmp_dir.exists():
                for f in self.tmp_dir.iterdir():
                    if f.is_file():
                        try:
                            f.unlink()
                        except Exception:
                            pass
        except Exception:
            pass

    def download_reel_audio(self, video_url: str) -> Optional[Tuple[bytes, str]]:
        """
        Descarga el audio de un Reel utilizando yt-dlp, lo lee en memoria y purga el archivo local.
        Retorna una tupla (audio_bytes, mime_type) o None si falla.
        """
        if not video_url:
            return None

        file_id = str(uuid.uuid4())
        out_template = str(self.tmp_dir / f"{file_id}.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": out_template,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }],
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "nocheckcertificate": True,
            "socket_timeout": 15,
        }

        downloaded_file = None
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            # Buscar el archivo generado (mp3 o m4a)
            candidates = list(self.tmp_dir.glob(f"{file_id}.*"))
            if candidates:
                downloaded_file = candidates[0]
                with open(downloaded_file, "rb") as f:
                    audio_data = f.read()

                suffix = downloaded_file.suffix.lower()
                mime = "audio/mp3" if suffix == ".mp3" else "audio/m4a"
                return audio_data, mime

        except Exception:
            # Fallback silencioso: no interrumpe el flujo si el video requiere login de Instagram
            pass
        finally:
            # Limpieza estricta de temporales del archivo específico
            candidates = list(self.tmp_dir.glob(f"{file_id}.*"))
            for f in candidates:
                try:
                    f.unlink()
                except Exception:
                    pass

        return None

media_extractor = MediaExtractor()
