#!/usr/bin/env python3
"""List pemstudy sync candidates in an Obsidian vault.

Usage: scan.py [vault_path]
    vault_path defaults to "vault_path" from ~/.pemstudy/config.json.

A note is a candidate when it has no `pem_synced` frontmatter or its mtime is
newer than `pem_synced`. Empty files and .obsidian/.trash/templates are skipped.

Output (tab-separated): STATUS <TAB> vault-relative-path
    CANDIDATE-NEW     never synced
    CANDIDATE-EDITED  edited since last sync
    OK                up to date
Exit code 0 always; parse stdout.
"""

import datetime
import json
import os
import re
import sys

SKIP_DIRS = {".obsidian", ".trash", "templates"}


def vault_from_config():
    try:
        with open(os.path.expanduser("~/.pemstudy/config.json")) as f:
            return json.load(f)["vault_path"]
    except (OSError, ValueError, KeyError):
        sys.exit("error: pass vault_path or run the setup skill to create ~/.pemstudy/config.json")


def main():
    vault = sys.argv[1] if len(sys.argv) > 1 else vault_from_config()
    vault = os.path.expanduser(vault)
    if not os.path.isdir(vault):
        sys.exit(f"error: vault not found: {vault}")
    for root, dirs, files in os.walk(vault):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, vault)
            if os.path.getsize(path) == 0:
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    head = f.read(2000)
            except (OSError, UnicodeDecodeError):
                continue
            m = re.search(r"^pem_synced:\s*(\S+)\s*$", head, re.M)
            if not m:
                print(f"CANDIDATE-NEW\t{rel}")
                continue
            try:
                synced = datetime.datetime.fromisoformat(m.group(1))
                if synced.tzinfo is None:
                    synced = synced.astimezone()  # treat naive as local
            except ValueError:
                print(f"CANDIDATE-EDITED\t{rel}")  # unparseable stamp: re-sync
                continue
            if os.path.getmtime(path) > synced.timestamp():
                print(f"CANDIDATE-EDITED\t{rel}")
            else:
                print(f"OK\t{rel}")


if __name__ == "__main__":
    main()
