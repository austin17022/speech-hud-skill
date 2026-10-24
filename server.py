#!/usr/bin/env python3
"""AI 演講分析 HUD 的本機伺服器：提供網頁，並接收錄好的影片存到 output/。"""
import http.server
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
import uuid

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "output")
JOBS = os.path.join(OUT, ".jobs")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8830
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"


def finish_job(d, q):
    """逐格輸出的畫面組成影片，接回原影片的聲音（延後開場秒數）。"""
    fps = q.get("fps", ["30"])[0]
    delay_ms = int(float(q.get("delay", ["0"])[0]) * 1000)
    name = q.get("name", ["recording"])[0]
    name = "".join(c for c in name if c not in '/\\:*?"<>|').strip() or "recording"
    out = os.path.join(OUT, f"{name}-{time.strftime('%Y%m%d-%H%M%S')}.mp4")
    video_args = ["-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    base = [FFMPEG, "-y", "-v", "error", "-framerate", fps, "-i", os.path.join(d, "f%05d.jpg")]
    src = os.path.join(d, "source")
    ok = False
    if os.path.exists(src):
        cmd = base + ["-i", src, "-filter_complex", f"[1:a]adelay=delays={delay_ms}:all=1[a]",
                      "-map", "0:v", "-map", "[a]", "-c:a", "aac", "-b:a", "192k"] + video_args + [out]
        ok = subprocess.run(cmd).returncode == 0
    if not ok:
        subprocess.run(base + video_args + [out], check=True)
    shutil.rmtree(d, ignore_errors=True)
    return out


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def reply(self, body):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode())

    def read_to(self, path):
        remaining = int(self.headers.get("Content-Length", 0))
        with open(path, "wb") as f:
            while remaining > 0:
                chunk = self.rfile.read(min(remaining, 1 << 20))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        parts = u.path.strip("/").split("/")
        q = urllib.parse.parse_qs(u.query)
        if u.path == "/job/start":
            jid = uuid.uuid4().hex[:12]
            os.makedirs(os.path.join(JOBS, jid))
            return self.reply(jid)
        if parts[0] == "job" and len(parts) >= 3:
            jid = parts[1]
            d = os.path.join(JOBS, jid)
            if not jid.isalnum() or not os.path.isdir(d):
                return self.send_error(404)
            if parts[2] == "frame" and len(parts) == 4 and parts[3].isdigit():
                self.read_to(os.path.join(d, f"f{int(parts[3]):05d}.jpg"))
                return self.reply("ok")
            if parts[2] == "source":
                self.read_to(os.path.join(d, "source"))
                return self.reply("ok")
            if parts[2] == "finish":
                return self.reply(finish_job(d, q))
            return self.send_error(404)
        if not u.path.startswith("/save"):
            self.send_error(404)
            return
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        ext = q.get("ext", ["webm"])[0]
        if ext not in ("webm", "mp4", "png", "jpg"):
            ext = "webm"
        name = q.get("name", ["recording"])[0]
        name = "".join(c for c in name if c not in '/\\:*?"<>|').strip() or "recording"
        os.makedirs(OUT, exist_ok=True)
        path = os.path.join(OUT, f"{name}-{time.strftime('%Y%m%d-%H%M%S')}.{ext}")
        size = int(self.headers.get("Content-Length", 0))
        with open(path, "wb") as f:
            remaining = size
            while remaining > 0:
                chunk = self.rfile.read(min(remaining, 1 << 20))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(path.encode())


if __name__ == "__main__":
    print(f"http://localhost:{PORT}")
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
