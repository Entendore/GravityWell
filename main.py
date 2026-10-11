#!/usr/bin/env python3
"""
Gravity Wells build helper.

  python build.py web       # HTML5 build via pygbag -> dist/GravityWells-web.zip
  python build.py desktop   # standalone binary via PyInstaller -> dist/
  python build.py all
"""
import os
import subprocess
import sys
import zipfile

APP = "GravityWells"
HERE = os.path.dirname(os.path.abspath(__file__))


def sh(cmd):
    print("+", " ".join(cmd))
    return subprocess.call(cmd, cwd=HERE)


def build_web():
    if sh([sys.executable, "-m", "pygbag", "--build", "."]) != 0:
        sys.exit("pygbag failed — run:  pip install pygbag")
    src = os.path.join(HERE, "build", "web")
    if not os.path.isdir(src):
        sys.exit("build/web not found — did pygbag run from the project folder?")
    out = os.path.join(HERE, "dist", APP + "-web.zip")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    # zip the CONTENTS so index.html sits at the zip root (itch requires this)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _dirs, files in os.walk(src):
            for f in files:
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, src))
    print("OK ->", out)


def build_desktop():
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
           "--onefile", "--windowed", "--name", APP, "main.py"]
    if sh(cmd) != 0:
        sys.exit("PyInstaller failed — run:  pip install pyinstaller")
    print("OK -> dist/  (zip the artifact per-OS before uploading to itch)")
    print("     tip: for debugging a blank window, drop --windowed to see the console.")


if __name__ == "__main__":
    what = (sys.argv[1] if len(sys.argv) > 1 else "all").lower()
    if what in ("web", "all"):
        build_web()
    if what in ("desktop", "all"):
        build_desktop()