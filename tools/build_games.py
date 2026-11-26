"""Build the home page game sections and the per-game pages from tools/games.json.

One source for every game, so the home page (stats, the featured highlights, the scrolling
row of the other games, footer links) and the page at /games/<slug>/ never drift apart. Clicking a game card on the home page opens
that game in a modal (the same card as its page); the link still works without script. The
home page is styled by assets/css/home.css, the game pages by assets/css/site.css. Edit
games.json, then run:

    python tools/build_games.py
    python tools/stamp_css.py      # only when a stylesheet in assets/css/ changed

games.json fields: slug, name, store_name, package, live (true = Google Play button and
"Maintained" on its page; false = "In development"), featured (true = one of the big
highlight cards on the home page, keep it to three; the rest go in the scrolling "More
games" row), genre, line
(one sentence on the home page card), about (two or three sentences on its page),
highlights (two or three short points listed under it), video. Art lives in assets/games/<slug>/ (icon.webp 256 px, feature.webp
1024x500).

video: "" shows the feature art only; a path such as "/assets/games/<slug>/gameplay.mp4"
shows that 9:16 gameplay clip (muted, looping, autoplay), with
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
    """Body shared by the home page modal and the game page: head, then the media beside (or above) the text."""
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


PLAY_ICON = (
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M4 3.5v17l9.2-8.5L4 '
    '3.5Zm10.4 9.6 2.6 2.4-10.7 6.1 8.1-8.5Zm0-2.2L6.3 2.4 17 8.5l-2.6 2.4Zm4.2-1.5 2.9 1.7c.7.4.7 1.4 0 1.8l-2.9 '
    '1.7-2.8-2.6 2.8-2.6Z"/></svg>'
)


def live_games() -> list:
    return [g for g in GAMES if g["live"]]


def dev_games() -> list:
    return [g for g in GAMES if not g["live"]]


def featured_games() -> list:
    return [g for g in GAMES if g.get("featured")]


def more_games() -> list:
    """Every game that is not featured: live ones first, then those in development."""
    rest = [g for g in GAMES if not g.get("featured")]
    return [g for g in rest if g["live"]] + [g for g in rest if not g["live"]]


def stats() -> str:
    """The three numbers under the hero."""
    rows = [(len(GAMES), "games made"), (len(live_games()), "live on Google Play"), (len(dev_games()), "coming soon")]
    cells = "".join(f"<div><b>{n}</b><span>{label}</span></div>" for n, label in rows)
    return f'        <div class="stats">{cells}</div>'


def featured_cards() -> str:
    """The highlight row (games.json "featured"): feature art, icon, genre and the Google Play button."""
    out = []
    for g in featured_games():
        slug = g["slug"]
        if g["live"]:
            chip_html = '<span class="chip on">Live</span>'
            action = (
                f'<a class="play" href="https://play.google.com/store/apps/details?id={g["package"]}" '
                f'rel="noopener">{PLAY_ICON}Get it on Google Play</a>'
            )
        else:
            chip_html = '<span class="chip">In development</span>'
            action = f'<a class="play" href="/games/{slug}/">See the game</a>'
        out.append(f"""        <article class="live-card">
          <a class="art" href="/games/{slug}/" data-game="{slug}"><img src="/assets/games/{slug}/feature.webp" alt="{e(g['name'])} feature art" width="1024" height="500" loading="lazy"></a>
          <div class="body">
            <img class="icon" src="/assets/games/{slug}/icon.webp" alt="{e(g['name'])} app icon" width="72" height="72">
            <div>
              <div class="meta">{chip_html}{e(g['genre'])}</div>
              <h3><a href="/games/{slug}/" data-game="{slug}">{e(g['name'])}</a></h3>
              <p>{e(g['line'])}</p>
              {action}
            </div>
          </div>
        </article>""")
    return "\n".join(out)


def more_cards() -> str:
    """The scrolling row under the highlights: every other game, feature art shown whole; only games in development
    carry a chip."""
    out = []
    for g in more_games():
        slug = g["slug"]
        art = (
            f'<img src="/assets/games/{slug}/feature.webp" alt="{e(g["name"])} feature art" width="1024" height="500" '
            'loading="lazy">'
        )
        chip_html = "" if g["live"] else '<span class="chip">In development</span>'
        out.append(f"""        <a class="dev-card" href="/games/{slug}/" data-game="{slug}">
          <div class="art">{art}{chip_html}</div>
          <div class="body">
            <div class="row"><img src="/assets/games/{slug}/icon.webp" alt="{e(g['name'])} app icon" width="40" height="40" loading="lazy"><div><h3>{e(g['name'])}</h3><span class="genre">{e(g['genre'])}</span></div></div>
            <p>{e(g['line'])}</p>
          </div>
        </a>""")
    return "\n".join(out)


def foot_games() -> str:
    links = [f'<li><a href="/games/{g["slug"]}/">{e(g["name"])}</a></li>' for g in live_games()]
    links.append('<li><a href="#games">All games</a></li>')
    return "\n".join("      " + link for link in links)


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
  document.querySelectorAll("a[data-game]").forEach((link) => {
    link.addEventListener("click", (event) => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      if (open(link.dataset.game)) event.preventDefault();
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


PAGE_FOOT = """<footer class="shell">
  <p class="footer-links">
    <a href="mailto:support@aftergamelab.com">Contact</a>
    <a href="https://github.com/Afterhours-Studio" rel="noopener">GitHub</a>
    <a class="to-top" href="#top">Back to top<svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M10 16V5M4.5 10.5 10 5l5.5 5.5"/></svg></a>
  </p>
  <p class="colophon">Afterhours Studio. Mobile games for Android, with iOS to follow.</p>
</footer>

</body>
</html>
"""


def main() -> None:
    index_path = ROOT / "index.html"
    index = index_path.read_text(encoding="utf-8")
    index = replace_block(index, "STATS", stats())
    index = replace_block(index, "FEATURED", featured_cards())
    index = replace_block(index, "MORE", more_cards())
    index = replace_block(index, "FOOTGAMES", foot_games())
    index = replace_block(index, "MODAL", modal())
    index_path.write_text(index, encoding="utf-8", newline="")

    foot = PAGE_FOOT
    for g in GAMES:
        out = ROOT / "games" / g["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page(g, PAGE_HEAD, foot), encoding="utf-8", newline="")
    print(f"built {len(GAMES)} games")


if __name__ == "__main__":
    main()
