"""Stamp the stylesheet link on every page with the stylesheet's own hash.

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
CSS = ROOT / "assets" / "css" / "site.css"
LINK = re.compile(r'(href="/assets/css/site\.css)(\?v=[0-9a-f]+)?(")')

digest = hashlib.sha256(CSS.read_bytes()).hexdigest()[:10]
changed = []

for page in sorted(ROOT.glob("**/*.html")):
    text = page.read_text(encoding="utf-8")
    stamped, n = LINK.subn(rf'\1?v={digest}\3', text)
    if n == 0:
        continue
    if stamped != text:
        page.write_text(stamped, encoding="utf-8", newline="")
        changed.append(page.relative_to(ROOT).as_posix())

print(f"site.css {digest}")
if changed:
    print("stamped: " + ", ".join(changed))
else:
    print("already current")

sys.exit(0)
