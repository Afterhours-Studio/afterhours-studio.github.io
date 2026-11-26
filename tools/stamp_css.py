"""Stamp each stylesheet link (site.css, home.css) on every page with that stylesheet's own hash.

GitHub Pages serves assets/css/site.css with a cache lifetime, so a browser
that has visited before keeps running the old stylesheet after a deploy: the
page is new, the layout rules are not. Giving the link a ?v= that changes with
the file content makes the browser fetch it again, and only then.

Run before committing a stylesheet change:

    python tools/stamp_css.py
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHEETS = ("site.css", "home.css")
changed = []

for sheet in SHEETS:
    digest = hashlib.sha256((ROOT / "assets" / "css" / sheet).read_bytes()).hexdigest()[:10]
    link = re.compile(rf'(href="/assets/css/{re.escape(sheet)})(\?v=[0-9a-f]+)?(")')
    for page in sorted(ROOT.glob("**/*.html")):
        if "mockup" in page.parts:
            continue
        text = page.read_text(encoding="utf-8")
        stamped, n = link.subn(rf"\1?v={digest}\3", text)
        if n and stamped != text:
            page.write_text(stamped, encoding="utf-8", newline="")
            changed.append(page.relative_to(ROOT).as_posix())
    print(f"{sheet} {digest}")
if changed:
    print("stamped: " + ", ".join(changed))
else:
    print("already current")

sys.exit(0)
