#!/usr/bin/env bash
# Encodes a 9:16 gameplay capture for the website: 540x960 H.264, fast start, quiet AAC track,
# plus a WebP poster from the first second. Then set "video" in tools/games.json and run
# tools/build_games.py.
#
#   bash tools/encode_gameplay.sh <capture.mp4> <slug>
#   -> assets/games/<slug>/gameplay.mp4 and gameplay.webp
set -euo pipefail
src="$1"
slug="$2"
root="$(cd "$(dirname "$0")/.." && pwd)"
out="$root/assets/games/$slug"
mkdir -p "$out"
ffmpeg -y -loglevel error -i "$src" \
  -vf "scale=540:960:force_original_aspect_ratio=decrease,pad=540:960:(ow-iw)/2:(oh-ih)/2,fps=30" \
  -c:v libx264 -preset slow -crf 27 -profile:v high -pix_fmt yuv420p -movflags +faststart \
  -c:a aac -b:a 96k -ac 2 \
  "$out/gameplay.mp4"
frame="$(mktemp -t gameplay).png"
ffmpeg -y -loglevel error -ss 1 -i "$out/gameplay.mp4" -frames:v 1 "$frame"
cwebp -quiet -q 80 "$frame" -o "$out/gameplay.webp"
rm -f "$frame"
ls -l "$out/gameplay.mp4" "$out/gameplay.webp"
