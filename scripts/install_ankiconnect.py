#!/usr/bin/env python3
"""Install the AnkiConnect add-on into Anki's add-ons folder.

Stdlib-only. The pemstudy plugin needs AnkiConnect (add-on code 2055492159) to talk
to Anki. This script downloads it and unzips it into the right place so the user
doesn't have to click through Anki's add-on manager — a fallback for when
`anki.py ping` reports the add-on is missing.

Usage:
    install_ankiconnect.py                 # detect profile dir, install if missing
    install_ankiconnect.py --dry-run       # show what it would do, touch nothing
    install_ankiconnect.py --profile-dir /path/to/Anki2   # non-standard install

It NEVER launches or modifies a running Anki; it only writes a fresh add-on directory.
Anki must be RESTARTED after this runs for the add-on to load.

Exit codes: 0 = installed or already present; non-zero = error (message on stderr).
"""

import argparse
import os
import sys
import urllib.error
import urllib.request
import zipfile
import io

ADDON_ID = "2055492159"
# AnkiWeb's download endpoint requires client-version params; a bare URL returns the
# ASCII string "Your version of Anki is too old." instead of the zip. The exact point
# version doesn't matter much, only that the shape is v=<major.minor>&p=<numeric>.
DOWNLOAD_URL = f"https://ankiweb.net/shared/download/{ADDON_ID}?v=2.1&p=260502"


def default_profile_dir():
    """Anki's base folder (contains addons21/), per platform."""
    home = os.path.expanduser("~")
    if sys.platform == "darwin":
        return os.path.join(home, "Library", "Application Support", "Anki2")
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming"))
        return os.path.join(base, "Anki2")
    # linux / other unix
    data = os.environ.get("XDG_DATA_HOME", os.path.join(home, ".local", "share"))
    return os.path.join(data, "Anki2")


def main():
    ap = argparse.ArgumentParser(description="Install the AnkiConnect add-on")
    ap.add_argument("--profile-dir", help="Anki2 base folder (default: OS standard)")
    ap.add_argument("--dry-run", action="store_true", help="report only; change nothing")
    args = ap.parse_args()

    profile_dir = args.profile_dir or default_profile_dir()
    addons_dir = os.path.join(profile_dir, "addons21")
    target = os.path.join(addons_dir, ADDON_ID)
    init_py = os.path.join(target, "__init__.py")

    print(f"platform:    {sys.platform}")
    print(f"Anki2 dir:   {profile_dir}")
    print(f"add-on dir:  {target}")

    if os.path.isfile(init_py):
        print("result:      already installed (AnkiConnect present) — nothing to do.")
        return 0

    if not os.path.isdir(profile_dir):
        sys.exit(
            f"error: Anki profile dir not found at {profile_dir}\n"
            "Open Anki once (so it creates its data folder), then re-run — or pass\n"
            "--profile-dir if your install is non-standard."
        )

    if args.dry_run:
        print("result:      DRY RUN — would download AnkiConnect and unzip into the "
              "add-on dir above.")
        return 0

    print("downloading AnkiConnect from AnkiWeb…")
    try:
        req = urllib.request.Request(DOWNLOAD_URL, headers={"User-Agent": "pemstudy"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
    except urllib.error.URLError as e:
        sys.exit(f"error: download failed ({e.reason}). Check your internet connection.")

    # AnkiWeb returns a short ASCII message instead of a zip on a bad request.
    if not data[:2] == b"PK":
        snippet = data[:120].decode("utf-8", "replace").strip()
        sys.exit(
            "error: AnkiWeb did not return a zip (got: "
            f"{snippet!r}).\nInstall manually instead: Anki → Tools → Add-ons → Get "
            f"Add-ons → paste {ADDON_ID} → restart Anki."
        )

    try:
        os.makedirs(target, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            # guard against zip-slip: no absolute or parent-escaping members
            for name in zf.namelist():
                dest = os.path.realpath(os.path.join(target, name))
                if not dest.startswith(os.path.realpath(target) + os.sep) and dest != os.path.realpath(target):
                    sys.exit(f"error: unsafe path in add-on zip: {name}")
            zf.extractall(target)
    except (OSError, zipfile.BadZipFile) as e:
        sys.exit(f"error: could not unpack add-on: {e}")

    print(f"result:      installed AnkiConnect into {target}")
    print("NEXT STEP:   restart Anki, then re-run the ping check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
