#!/usr/bin/env python3
"""Rebuild the "Free tools" grid in README.md from tools.json.

Only repos that are public right now are shown. A private, renamed or
deleted repo is left out, and it comes back on its own once it is public.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

OWNER = "NIDACADEMY"
ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
TOOLS = ROOT / "tools.json"
START = "<!-- TOOLS:START -->"
END = "<!-- TOOLS:END -->"
# "gallery": borderless banners side by side, each linking to its repo.
# "cards":   2-column table with a title line and Download / Star badges.
LAYOUT = "gallery"


def is_public(repo):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{OWNER}/{repo}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-tools"},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return not json.load(resp).get("private", True)
    except urllib.error.HTTPError as e:
        if e.code == 404:  # private repos look like 404 to outsiders
            return False
        raise  # rate limit or outage: fail instead of emptying the grid


def card(t):
    base = f"https://github.com/{OWNER}/{t['repo']}"
    n = t["name"]
    # The banner already shows the name and description, so the card only
    # adds one title line and two small badges under it.
    download = (
        f"https://img.shields.io/github/v/release/{OWNER}/{t['repo']}"
        f"?style=flat-square&label=Download&color={t['color']}"
        f"&logo=github&logoColor=white"
    )
    stars = (
        f"https://img.shields.io/github/stars/{OWNER}/{t['repo']}"
        f"?style=flat-square&label=Star&color=3b3b3b&logo=github&logoColor=white"
    )
    return f"""    <td width="50%" valign="top">
      <a href="{base}"><img src="{base}/raw/main/{t['banner']}" alt="{t['alt']}: {t['description']}"></a>
      <p><a href="{base}"><b>{n}</b></a> · {t['type']}</p>
      <p>
        <a href="{base}/releases/latest/download/{t['zip']}"><img src="{download}" alt="Download {n}"></a>
        <a href="{base}"><img src="{stars}" alt="Star {n} on GitHub"></a>
      </p>
    </td>"""


def render(tools):
    return render_gallery(tools) if LAYOUT == "gallery" else render_cards(tools)


def render_gallery(tools):
    """Banners side by side, no table, so GitHub draws no borders.
    Each banner links to its repo, where the download button lives."""
    imgs = []
    for t in tools:
        base = f"https://github.com/{OWNER}/{t['repo']}"
        alt = f"{t['name']}, {t['type']}: {t['description']}"
        imgs.append(
            f'  <a href="{base}" title="{t["name"]} · {t["type"]}">'
            f'<img src="{base}/raw/main/{t["banner"]}" alt="{alt}" width="49%"></a>'
        )
    return '<p align="center">\n' + "\n".join(imgs) + "\n</p>"


def render_cards(tools):
    rows = []
    for i in range(0, len(tools), 2):
        pair = [card(t) for t in tools[i:i + 2]]
        if len(pair) == 1:
            pair.append('    <td width="50%" valign="top"></td>')
        rows.append("  <tr>\n" + "\n".join(pair) + "\n  </tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def main():
    tools = json.loads(TOOLS.read_text())
    shown = []
    for t in tools:
        public = is_public(t["repo"])
        print(f"{'show' if public else 'hide'}  {t['repo']}")
        if public:
            shown.append(t)

    text = README.read_text()
    if START not in text or END not in text:
        sys.exit(f"README.md is missing the {START} / {END} markers")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    new = f"{head}{START}\n{render(shown)}\n{END}{tail}"

    if new != text:
        README.write_text(new)
        print("README.md updated")
    else:
        print("README.md already up to date")


if __name__ == "__main__":
    main()
