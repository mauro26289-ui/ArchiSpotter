# ArchiSpotter — ElevenLabs + GitHub Actions

This package adds an **on-demand** GitHub Actions workflow for generating MP3 narration files. It does **not** modify your current ArchiSpotter HTML or automatically publish audio. The included narration JSON contains **one pilot monument (Colosseum), in three languages**; the other 99 monuments must be scripted and reviewed before batch generation.

## Install in your existing GitHub Pages repository

1. Upload the `.github/workflows/generate-audioguides.yml` file preserving its directory path (the dot in `.github` matters).
2. Upload `scripts/generate_audio.py` and `narrations/scripts.json` preserving their directory paths.
3. Go to repository **Settings → Secrets and variables → Actions → New repository secret**. Name it `ELEVENLABS_API_KEY` and paste your ElevenLabs API key there. **Never put the API key in index.html or in the narration JSON.**
4. Go to **Actions → Generate ArchiSpotter audioguides → Run workflow**. Start with `monument_id=colosseum` and `dry_run=true` (free preview, no API call).
5. When preview works, run it again with `dry_run=false`. This generates three MP3s and uses ElevenLabs credits.
6. When the job finishes, open its run page and download the `archispotter-audioguides` artifact. Unzip it and upload the MP3s to an `audio/` folder in your GitHub Pages repository.
7. **Audio playback is not yet wired into the app.** Next, adapt the HTML player to load `audio/colosseum-es.mp3`, `audio/colosseum-en.mp3`, `audio/colosseum-it.mp3` by selected language, and fall back to browser speech if an audio file is missing.

## Extending to 100 monuments

Add an object to `narrations/scripts.json` for each monument, with a stable unique `id` matching the app's monument ID and `narrations` keys `es`, `en`, and `it`. Check historical accuracy and pronunciation before generation. The script skips files that already exist **in the current job workspace**. Note that GitHub Actions runners are fresh each run; the artifact is not restored automatically. To avoid paying again, generate only missing monument IDs or use a workflow enhancement to restore existing audio.

## Voice mapping

- English: Maya (`zzAIcrq5pp7webLI6ptl`)
- Spanish: Luisa (`7nCYbNPCi8RLAKVnYEoO`)
- Italian: Michele (`Dl7eCteSx0r4bKkraGGE`)

Voice access, available models, credit consumption and account permissions depend on ElevenLabs. This workflow uses `eleven_multilingual_v2`. Do a 3-audio pilot before any large batch. The API key is stored only in GitHub Actions secrets.

## Notes

- Audio artifacts expire after 30 days unless downloaded and committed to the repository.
- This workflow has read-only repository permissions; it cannot accidentally overwrite your website.
- GitHub Pages serves committed MP3s; artifacts alone do not publish them.
- If your GitHub account uses a branch-based Pages deployment, keep `index.html` and `audio/` in the published branch/folder.
