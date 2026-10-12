# AGENTS.md

## Unwritten
- Publishing: pushing a `v*` tag runs `.github/workflows/release.yml`, which builds `Tekken8Assistant.exe` on Windows with PyInstaller and bundled Tesseract and attaches it to a GitHub Release; a tag is a release.
- Gotchas: the PyInstaller command lives twice, in `release.yml` and `tools/build_exe.ps1` (their `--exclude-module` lists already differ by `notebook`); change both. `tekken_assistant/data/cache/*.json` is the kage combo cache (24 h TTL) that a source run rewrites; the root-anchored `data/cache/` line in `.gitignore` does not cover it, so keep cache churn out of commits.
- Checks: `python -m pytest tests/ -q` (the only CI job, Ubuntu, Python 3.12). Capture, hotkeys, and the overlay need Windows and a running game, so CI does not exercise them.
- Conventions: README, installer messages, and commit descriptions are in Russian, with conventional-commit prefixes. A character is one JSON file in `tekken_assistant/data/characters/`: `aliases` feed OCR name matching and `kage_slug` picks the kagewebsite combo page. The loader skips a malformed file with only a console print, so run `tests/test_loader.py` after editing one (adding a character also bumps its `EXPECTED_COUNT`).

## Pointers
- **Writing** or reviewing code: apply `CODING_STANDARDS.md`; project config and linters win where they disagree.
- **Security**-sensitive change (auth, permissions, untrusted input, secrets): read `docs/agents/security.md` first.
- **Committing** or opening a PR: follow `docs/agents/git.md`.
- **Risky** change (spans modules, migrates data, alters a public API): propose a phased plan and get approval before editing.
- **Done** means you ran the project's own check commands and they are green, or you named the ones you could not run.
