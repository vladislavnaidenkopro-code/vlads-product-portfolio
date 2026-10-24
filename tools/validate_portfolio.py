from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]

EXPECTED = {
    "README.md",
    "PUBLIC_DISCLOSURE.md",
    "products/universal-browser-agent.md",
    "products/vlads-live-assistant.md",
    "products/vlads-forecast-intelligence.md",
    "products/vlads-technology-intelligence.md",
    "products/vlads-operator-studio.md",
    "assets/cover.jpg",
    "assets/universal-browser-agent.jpg",
    "assets/vlads-live-assistant.jpg",
    "assets/vlads-forecast-intelligence.jpg",
    "assets/vlads-technology-intelligence.jpg",
    "assets/vlads-operator-studio.jpg",
}

MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
WINDOWS_PATH = re.compile(r"\b[A-Za-z]:\\")
WINDOWS_MACHINE = re.compile(r"\bDESKTOP-[A-Z0-9-]+\b", re.IGNORECASE)
TAILNET_HOST = re.compile(r"\b[a-z0-9-]+\.ts\.net\b", re.IGNORECASE)
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
PRIVATE_MARKERS = (
    "/home/",
    "localhost:",
    "127.0.0.1",
)

errors: list[str] = []

for rel in sorted(EXPECTED):
    if not (ROOT / rel).exists():
        errors.append(f"missing expected file: {rel}")

for md in sorted(ROOT.rglob("*.md")):
    rel = md.relative_to(ROOT)
    text = md.read_text(encoding="utf-8")

    if WINDOWS_PATH.search(text):
        errors.append(f"{rel}: contains a Windows absolute path")
    if WINDOWS_MACHINE.search(text):
        errors.append(f"{rel}: contains a Windows machine identifier")
    if TAILNET_HOST.search(text):
        errors.append(f"{rel}: contains a private tailnet hostname")
    if IPV4.search(text):
        errors.append(f"{rel}: contains an IPv4 address")
    for marker in PRIVATE_MARKERS:
        if marker.lower() in text.lower():
            errors.append(f"{rel}: contains private infrastructure marker {marker!r}")

    for raw_target in MARKDOWN_LINK.findall(text):
        target = raw_target.strip().split()[0].strip("<>")
        if not target or target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        target = unquote(target.split("#", 1)[0])
        resolved = (md.parent / target).resolve()
        try:
            resolved.relative_to(ROOT)
        except ValueError:
            errors.append(f"{rel}: local link escapes repository: {target}")
            continue
        if not resolved.exists():
            errors.append(f"{rel}: broken local link: {target}")

if errors:
    print("Portfolio QA: FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("Portfolio QA: PASS")
print(f"Checked {len(EXPECTED)} expected artifacts and all Markdown local links.")
