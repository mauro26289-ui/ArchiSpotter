#!/usr/bin/env python3
"""Generate ArchiSpotter narration MP3s with ElevenLabs. Stdlib only."""
import argparse
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
VOICES = {
    "en": "zzAIcrq5pp7webLI6ptl",  # Maya
    "it": "nH7uLS5UdEnvKEOAXtlQ",  # Vittorio
    "es": "7nCYbNPCi8RLAKVnYEoO",  # Luisa
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(ROOT / "narrations" / "scripts.json"))
    ap.add_argument("--output", default=str(ROOT / "audio"))
    ap.add_argument("--only", default="", help="Optional monument id")
    ap.add_argument("--force", action="store_true", help="Regenerate existing files (costs credits)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    data = json.loads(pathlib.Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("scripts.json must be an array")
    out = pathlib.Path(args.output)
    tasks = []
    seen = set()
    for monument in data:
        slug = monument.get("id", "")
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", slug):
            raise ValueError(f"Invalid monument id: {slug!r}")
        if args.only and slug != args.only:
            continue
        for lang, voice in VOICES.items():
            narrative = monument.get("narrations", {}).get(lang, "").strip()
            if not narrative:
                continue
            key = (slug, lang)
            if key in seen:
                raise ValueError(f"Duplicate audio: {slug}/{lang}")
            seen.add(key)
            path = out / f"{slug}-{lang}.mp3"
            tasks.append((slug, lang, voice, narrative, path))
    if args.only and not tasks:
        raise ValueError(f"No narration found for {args.only!r}")
    print(f"Prepared {len(tasks)} narration(s).")
    missing = [(s, l, v, t, p) for s, l, v, t, p in tasks if args.force or not p.is_file() or p.stat().st_size == 0]
    print(f"To generate: {len(missing)}; already present: {len(tasks)-len(missing)}")
    if args.dry_run:
        for _, _, _, _, p in missing:
            print(f"DRY RUN: {p.name}")
        return
    if not missing:
        return
    key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY secret is missing")
    out.mkdir(parents=True, exist_ok=True)
    for idx, (slug, lang, voice, narrative, path) in enumerate(missing, 1):
        print(f"[{idx}/{len(missing)}] Generating {path.name} ({len(narrative)} characters)", flush=True)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128"
        payload = json.dumps({
            "text": narrative,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.55, "similarity_boost": 0.80, "style": 0.10, "use_speaker_boost": True},
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, method="POST", headers={
            "xi-api-key": key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        })
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=120) as response:
                    audio = response.read()
                if len(audio) < 1000:
                    raise RuntimeError("Unexpectedly small audio response")
                temp = path.with_suffix(".mp3.part")
                temp.write_bytes(audio)
                temp.replace(path)
                break
            except urllib.error.HTTPError as exc:
                detail = exc.read(800).decode("utf-8", "replace")
                if exc.code in (401, 402, 403, 422):
                    raise RuntimeError(f"ElevenLabs HTTP {exc.code} for {path.name}: {detail}") from None
                if attempt == 3:
                    raise RuntimeError(f"ElevenLabs HTTP {exc.code}: {detail}") from None
                time.sleep(2 ** attempt * 3)
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt * 3)
    print("Generation complete.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
