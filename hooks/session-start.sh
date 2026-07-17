#!/bin/sh
# pemstudy SessionStart hook: nudge first-time users toward setup.
#
# If the plugin hasn't been configured yet (~/.pemstudy/config.json is absent),
# print a one-line note. SessionStart stdout is added to the session context, so
# Claude sees it and can proactively offer to run /pemstudy:setup. If config exists,
# print nothing. Always exit 0 — a hook must never block the session.
#
# Pure POSIX sh with a single file test, so it runs anywhere (macOS, Linux, and
# Git Bash on Windows) without needing Python on the hot path.

if [ ! -f "$HOME/.pemstudy/config.json" ]; then
  echo "pemstudy is installed but not yet configured (no ~/.pemstudy/config.json). Offer to run /pemstudy:setup, which verifies AnkiConnect (installing it if needed), asks for the user's Obsidian vault, and creates the deck tree + note types."
fi

exit 0
