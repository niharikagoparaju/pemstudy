#!/usr/bin/env python3
"""AnkiConnect client CLI for the pemstudy plugin.

Stdlib-only (no pip installs). Talks to the AnkiConnect add-on
(https://ankiweb.net/shared/info/2055492159) over its local HTTP API.

Usage:
    anki.py ping
    anki.py decks
    anki.py models
    anki.py model-fields "PEM Basic"
    anki.py create-deck "PEM Boards::01 Emergency Conditions"
    anki.py find 'deck:"PEM Boards" tag:pem::outline::01-emergency-conditions::h-infectious-disease'
    anki.py notes-info 1234567890 1234567891
    anki.py cards-info 1234567890
    anki.py add-note --json '{"deckName": ..., "modelName": ..., "fields": {...}, "tags": [...]}'
    anki.py add-notes --json '[{note}, {note}, ...]'
    anki.py update-note --json '{"id": 123, "fields": {...}, "tags": [...]}'
    anki.py delete-notes 1234567890 1234567891
    anki.py add-tags --notes 123,456 --tags "pem::flagged"
    anki.py remove-tags --notes 123,456 --tags "pem::flagged"
    anki.py change-deck --cards 123,456 --deck "PEM Boards::03 Trauma"
    anki.py store-media /path/to/image.png [--name stored-name.png]
    anki.py create-model --json '{"modelName": ..., "inOrderFields": [...], "cardTemplates": [...]}'
    anki.py export-backup /path/to/backup.apkg [--deck "PEM Boards"]
    anki.py invoke <action> [--json '<params>']    # escape hatch for any AnkiConnect action

JSON parameters may be passed via --json '<literal>' or --json-file <path>.
Output is always JSON on stdout. Errors exit non-zero with a message on stderr.

Config: reads ~/.pemstudy/config.json for "ankiconnect_url" (default
http://127.0.0.1:8765). Override with --url or PEMSTUDY_ANKICONNECT_URL.
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

ANKICONNECT_VERSION = 6
DEFAULT_URL = "http://127.0.0.1:8765"
CONFIG_PATH = os.path.expanduser("~/.pemstudy/config.json")


def resolve_url(cli_url):
    if cli_url:
        return cli_url
    env = os.environ.get("PEMSTUDY_ANKICONNECT_URL")
    if env:
        return env
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f).get("ankiconnect_url") or DEFAULT_URL
    except (OSError, ValueError):
        return DEFAULT_URL


def invoke(url, action, params=None):
    payload = json.dumps(
        {"action": action, "version": ANKICONNECT_VERSION, "params": params or {}}
    ).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.load(resp)
    except urllib.error.URLError as e:
        sys.exit(
            f"error: cannot reach AnkiConnect at {url} ({e.reason}).\n"
            "Is Anki open? Is the AnkiConnect add-on installed (code 2055492159)?"
        )
    if body.get("error"):
        sys.exit(f"error: AnkiConnect: {body['error']}")
    return body.get("result")


def load_json_arg(args, required=True):
    """Return parsed JSON from --json or --json-file."""
    if getattr(args, "json", None) is not None:
        raw = args.json
    elif getattr(args, "json_file", None):
        with open(args.json_file) as f:
            raw = f.read()
    elif required:
        sys.exit("error: --json or --json-file is required for this command")
    else:
        return None
    try:
        return json.loads(raw)
    except ValueError as e:
        sys.exit(f"error: invalid JSON: {e}")


def emit(result):
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def int_list(values):
    try:
        return [int(v) for v in values]
    except ValueError:
        sys.exit("error: note/card ids must be integers")


def csv_int_list(value):
    return int_list(value.split(","))


def main():
    parser = argparse.ArgumentParser(
        description="AnkiConnect client for the pemstudy plugin"
    )
    parser.add_argument("--url", help="AnkiConnect URL (default: config or %s)" % DEFAULT_URL)
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name, **kwargs):
        p = sub.add_parser(name, **kwargs)
        return p

    add("ping", help="check AnkiConnect is reachable; prints its API version")
    add("decks", help="list all deck names")
    add("models", help="list all note type (model) names")

    p = add("model-fields", help="list field names of a note type")
    p.add_argument("model")

    p = add("create-deck", help="create a deck (idempotent)")
    p.add_argument("deck")

    p = add("find", help="find note ids matching an Anki search query")
    p.add_argument("query")

    p = add("notes-info", help="full field/tag info for note ids")
    p.add_argument("ids", nargs="+")

    p = add("cards-info", help="card-level info (deck, due, etc.) for card ids")
    p.add_argument("ids", nargs="+")

    for name, help_text in [
        ("add-note", "add one note; --json is the AnkiConnect note object"),
        ("add-notes", "add many notes; --json is a list of note objects"),
        ("update-note", 'update fields/tags; --json {"id":..., "fields":..., "tags":...}'),
        ("create-model", "create a note type; --json is the createModel params object"),
    ]:
        p = add(name, help=help_text)
        p.add_argument("--json")
        p.add_argument("--json-file")

    p = add("delete-notes", help="delete notes by id (irreversible; back up first)")
    p.add_argument("ids", nargs="+")

    p = add("add-tags", help="add tags to notes")
    p.add_argument("--notes", required=True, help="comma-separated note ids")
    p.add_argument("--tags", required=True, help="space-separated tag string")

    p = add("remove-tags", help="remove tags from notes")
    p.add_argument("--notes", required=True, help="comma-separated note ids")
    p.add_argument("--tags", required=True, help="space-separated tag string")

    p = add("change-deck", help="move cards to another deck")
    p.add_argument("--cards", required=True, help="comma-separated card ids")
    p.add_argument("--deck", required=True)

    p = add("store-media", help="upload a file into Anki's media collection")
    p.add_argument("path")
    p.add_argument("--name", help="filename to store as (default: basename)")

    p = add("export-backup", help="export a deck (default: whole collection deck tree) to .apkg")
    p.add_argument("path")
    p.add_argument("--deck", default=None, help="deck name to export (omit for all)")

    p = add("invoke", help="raw AnkiConnect action (escape hatch)")
    p.add_argument("action")
    p.add_argument("--json")
    p.add_argument("--json-file")

    args = parser.parse_args()
    url = resolve_url(args.url)
    cmd = args.command

    if cmd == "ping":
        emit({"ankiconnect_version": invoke(url, "version")})
    elif cmd == "decks":
        emit(invoke(url, "deckNames"))
    elif cmd == "models":
        emit(invoke(url, "modelNames"))
    elif cmd == "model-fields":
        emit(invoke(url, "modelFieldNames", {"modelName": args.model}))
    elif cmd == "create-deck":
        emit(invoke(url, "createDeck", {"deck": args.deck}))
    elif cmd == "find":
        emit(invoke(url, "findNotes", {"query": args.query}))
    elif cmd == "notes-info":
        emit(invoke(url, "notesInfo", {"notes": int_list(args.ids)}))
    elif cmd == "cards-info":
        emit(invoke(url, "cardsInfo", {"cards": int_list(args.ids)}))
    elif cmd == "add-note":
        emit(invoke(url, "addNote", {"note": load_json_arg(args)}))
    elif cmd == "add-notes":
        emit(invoke(url, "addNotes", {"notes": load_json_arg(args)}))
    elif cmd == "update-note":
        note = load_json_arg(args)
        # updateNoteFields only touches fields; handle tags too if provided.
        if "fields" in note:
            invoke(url, "updateNoteFields", {"note": {"id": note["id"], "fields": note["fields"]}})
        if "tags" in note:
            info = invoke(url, "notesInfo", {"notes": [note["id"]]})
            old_tags = info[0]["tags"] if info else []
            if old_tags:
                invoke(url, "removeTags", {"notes": [note["id"]], "tags": " ".join(old_tags)})
            if note["tags"]:
                invoke(url, "addTags", {"notes": [note["id"]], "tags": " ".join(note["tags"])})
        emit({"updated": note["id"]})
    elif cmd == "create-model":
        emit(invoke(url, "createModel", load_json_arg(args)))
    elif cmd == "delete-notes":
        invoke(url, "deleteNotes", {"notes": int_list(args.ids)})
        emit({"deleted": int_list(args.ids)})
    elif cmd == "add-tags":
        invoke(url, "addTags", {"notes": csv_int_list(args.notes), "tags": args.tags})
        emit({"tagged": csv_int_list(args.notes), "tags": args.tags})
    elif cmd == "remove-tags":
        invoke(url, "removeTags", {"notes": csv_int_list(args.notes), "tags": args.tags})
        emit({"untagged": csv_int_list(args.notes), "tags": args.tags})
    elif cmd == "change-deck":
        invoke(url, "changeDeck", {"cards": csv_int_list(args.cards), "deck": args.deck})
        emit({"moved": csv_int_list(args.cards), "deck": args.deck})
    elif cmd == "store-media":
        with open(args.path, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")
        name = args.name or os.path.basename(args.path)
        stored = invoke(url, "storeMediaFile", {"filename": name, "data": data})
        emit({"stored": stored})
    elif cmd == "export-backup":
        deck = args.deck
        path = os.path.abspath(args.path)
        if deck:
            ok = invoke(url, "exportPackage", {"deck": deck, "path": path, "includeSched": True})
            emit({"exported": deck, "path": path, "ok": ok})
        else:
            results = {}
            for d in invoke(url, "deckNames"):
                if "::" in d:
                    continue  # top-level decks include their subdecks
                deck_path = path.replace(".apkg", f"-{d.replace(' ', '_')}.apkg")
                results[d] = {
                    "path": deck_path,
                    "ok": invoke(url, "exportPackage", {"deck": d, "path": deck_path, "includeSched": True}),
                }
            emit({"exported": results})
    elif cmd == "invoke":
        emit(invoke(url, args.action, load_json_arg(args, required=False)))


if __name__ == "__main__":
    main()
