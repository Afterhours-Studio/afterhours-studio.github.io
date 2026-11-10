"""Build the games list, the game modal and the per-game pages from tools/games.json.

One source for every game, so the plate on the home page, the modal it opens and the
page at /games/<slug>/ never drift apart. Edit games.json, then run:

    python tools/build_games.py
    python tools/stamp_css.py      # only when assets/css/site.css changed

games.json fields: slug, name, store_name, package, live (true = "Maintained", false =
"In development"), genre, line (one sentence on the plate), about (two or three sentences
in the modal), highlights (two or three short points listed under it), video. Art lives in assets/games/<slug>/ (icon.webp 256 px, feature.webp
1024x500).

video: "" shows the feature art only; a path such as "/assets/games/<slug>/gameplay.mp4"
shows that 9:16 gameplay clip (muted, looping, autoplay when the card opens), with
assets/games/<slug>/gameplay.webp as its poster when present. Encode clips with
tools/encode_gameplay.sh.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMES = json.loads((ROOT / "tools" / "games.json").read_text(encoding="utf-8"))
SITE = "https://afterhours-studio.github.io"

ARROW = (
    '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
    '<path d="M4 10h11M10.5 5.5 15 10l-4.5 4.5"/></svg>'
)


def e(text: str) -> str:
    return html.escape(text, quote=True)


def chip(g: dict) -> str:
    return "Maintained" if g["live"] else "In development"


def media(g: dict) -> str:
    """The gameplay video (9:16, muted, looping) when there is one, else the plain feature art."""
    slug = g["slug"]
    video = g.get("video", "")
    if not video:
        return (
            f'<div class="media feature-art"><img src="/assets/games/{slug}/feature.webp" '
            f'alt="{e(g["name"])} feature art" width="1024" height="500" loading="lazy"></div>'
        )
    poster = f"/assets/games/{slug}/gameplay.webp"
    poster_attr = f' poster="{poster}"' if (ROOT / poster.lstrip("/")).exists() else ""
    return (
        f'<div class="media gameplay"><video src="{e(video)}"{poster_attr} autoplay muted loop playsinline '
        f'controls preload="metadata" aria-label="{e(g["name"])} gameplay"></video></div>'
    )


def card(g: dict, heading: str) -> str:
    """Body shared by the modal and the page: head, then the media beside (or above) the text."""
    play_url = f"https://play.google.com/store/apps/details?id={g['package']}"
    note = "" if g["live"] else '<p class="note">The Google Play link works once the game is published.</p>'
    layout = "card-body has-video" if g.get("video") else "card-body"
    points = "".join(f"<li>{e(p)}</li>" for p in g.get("highlights", []))
    points = f'<ul class="card-points">{points}</ul>' if points else ""
    return f"""<div class="card-head">
      <img src="/assets/games/{g['slug']}/icon.webp" alt="{e(g['name'])} app icon" width="72" height="72">
      <div>
        <span class="chip">{chip(g)}</span>
        <{heading}>{e(g['name'])}</{heading}>
        <p class="card-meta">{e(g['genre'])} · Android</p>
      </div>
    </div>
    <div class="{layout}">
      {media(g)}
      <div class="card-text">
        <p class="card-about">{e(g['about'])}</p>
        {points}
        <p class="actions">
          <a class="btn primary" href="{play_url}" rel="noopener">Google Play</a>
          <span class="btn disabled" aria-disabled="true" title="Coming later">App Store</span>
        </p>
        {note}
      </div>
    </div>"""


def plates() -> str:
    out = []
    for g in GAMES:
        out.append(f"""      <a class="plate" href="/games/{g['slug']}/" data-game="{g['slug']}">
        <img src="/assets/games/{g['slug']}/icon.webp" alt="{e(g['name'])} app icon" width="76" height="76" loading="lazy">
        <div>
          <div class="plate-top">
            <span class="chip">{chip(g)}</span>
            <span class="go">{ARROW}</span>
          </div>
          <h2>{e(g['name'])}</h2>
          <p>{e(g['line'])}</p>
        </div>
      </a>
""")
    return "\n".join(out)


MODAL_SCRIPT = """<script>
(() => {
  const dialog = document.getElementById("game-modal");
  const body = dialog.querySelector(".game-modal-body");
  const open = (slug) => {
    const tpl = document.getElementById("game-" + slug);
    if (!tpl || typeof dialog.showModal !== "function") return false;
    body.replaceChildren(tpl.content.cloneNode(true));
    dialog.showModal();
    history.replaceState(null, "", "#" + slug);
    return true;
  };
  document.querySelectorAll("a.plate[data-game]").forEach((plate) => {
    plate.addEventListener("click", (event) => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      if (open(plate.dataset.game)) event.preventDefault();
    });
  });
  dialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); });
  dialog.querySelector(".game-modal-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", () => {
    body.replaceChildren();
    history.replaceState(null, "", location.pathname + location.search);
  });
  const fromHash = () => { const slug = location.hash.slice(1); if (slug && !dialog.open) open(slug); };
  window.addEventListener("hashchange", fromHash);
  fromHash();
})();
</script>"""


def modal() -> str:
    templates = "\n".join(
        f'<template id="game-{g["slug"]}">\n    {card(g, "h2")}\n</template>' for g in GAMES
    )
    return f"""<dialog class="game-modal" id="game-modal" aria-label="Game details">
  <button class="game-modal-close" type="button" aria-label="Close">&times;</button>
  <div class="game-modal-body"></div>
</dialog>
{templates}
{MODAL_SCRIPT}"""


def replace_block(text: str, name: str, content: str) -> str:
    pattern = re.compile(rf"(<!-- {name}:START -->\n).*?([ \t]*<!-- {name}:END -->)", re.S)
    new, n = pattern.subn(lambda m: m.group(1) + content.rstrip("\n") + "\n" + m.group(2), text)
    if n != 1:
        raise SystemExit(f"index.html: marker {name} not found")
    return new


def page(g: dict, shell_head: str, foot: str) -> str:
    head = shell_head
    for old, new in {
        "__TITLE__": e(f"{g['name']} - Afterhours Studio"),
        "__DESC__": e(f"{g['name']} by Afterhours Studio: {g['line']}"),
        "__NAME__": e(g["name"]),
        "__LINE__": e(g["line"]),
        "__SLUG__": g["slug"],
    }.items():
        head = head.replace(old, new)
    return f"""{head}
<main class="shell">

  <a class="back" href="/#games">All games</a>

  <article class="game-page rise">
    {card(g, "h1")}
  </article>

</main>
{foot}"""


PAGE_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<link rel="canonical" href="SITE/games/__SLUG__/">
<meta property="og:type" content="website">
<meta property="og:title" content="__NAME__">
<meta property="og:description" content="__LINE__">
<meta property="og:url" content="SITE/games/__SLUG__/">
<meta property="og:image" content="SITE/assets/games/__SLUG__/feature.webp">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/games/__SLUG__/icon.webp" type="image/webp">
<link rel="preload" href="/assets/fonts/fraunces-var-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/karla-var-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.css">
</head>
<body>

<header class="shell masthead" id="top">
  <a class="wordmark" href="/">Afterhours Studio</a>
  <nav>
    <a href="/#games">Games</a>
    <a href="/privacy/">Privacy</a>
    <a href="/terms/">Terms</a>
  </nav>
</header>
""".replace("SITE", SITE)


def main() -> None:
    index_path = ROOT / "index.html"
    index = index_path.read_text(encoding="utf-8")
    index = replace_block(index, "GAMES", plates().rstrip("\n"))
    index = replace_block(index, "MODAL", modal())
    index_path.write_text(index, encoding="utf-8", newline="")

    foot = index[index.index("<footer") :]
    foot = foot[: foot.index("</footer>") + len("</footer>")] + "\n\n</body>\n</html>\n"
    for g in GAMES:
        out = ROOT / "games" / g["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page(g, PAGE_HEAD, foot), encoding="utf-8", newline="")
    print(f"built {len(GAMES)} games")


if __name__ == "__main__":
    main()
