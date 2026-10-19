# PLUZ5-Cust

Your own PS5 payload store, kept fresh by GitHub. **No payloads are shipped.** You pick the sources,
GitHub Actions checks them daily and writes a manifest that
[pldmgr](https://github.com/itsPLK/ps5-payload-manager) on your PS5 reads.

```
builder.html ─► payload_registry.json ─► configs/ ─► Actions (fetch, build, validate) ─► manifests/PLUZ-ps5-Source.json ─► pldmgr
```

## 1 · Get your copy (10 min, browser only)

| # | Do this | Where |
|---|---|---|
| 1 | **Use this template → Create a new repository** (Public) | this repo |
| 2 | **Settings → Actions → General → Workflow permissions → Read and write → Save** | your repo |
| 3 | **Settings → Pages → Source: Deploy from a branch → Branch `main` → `/ (root)` → Save**. Wait for the green "site is live" box (1-3 min) | your repo |

## 2 · Build your list

Open `https://<you>.github.io/<repo>/web/builder.html`

1. Type your **store name** (shown in pldmgr).
2. Paste GitHub repo URLs, one per line → **Add**. Or **Load example list** for a ready-made start.
3. Tidy the cards: category, FW min/max, hardware tag. Use the **Info %** badge to find thin entries; sort by it.
4. **Download payload_registry.json**.

## 3 · Publish it

1. In your repo open `configs/` → **Add file → Upload files** → drop `payload_registry.json` → **Commit**.
2. **Actions → PLUZ5 Update → Run workflow.** Green tick in about a minute. (Then it runs daily and on every change.)
3. Check `manifests/PLUZ-ps5-Source.json` exists. `[SKIP]` lines in the log say what to fix (see Troubleshooting).

## 4 · Use it on the PS5

pldmgr → add a custom repository (open the link in a browser first; you should see JSON):

```
https://raw.githubusercontent.com/<you>/<repo>/main/manifests/PLUZ-ps5-Source.json
```

**Edit later:** builder → section 3 fill user + repo → **Load from my repo** → change → Download → upload to `configs/` again.

## 5 · Add your own .elf / .bin

For a file that is not on GitHub (your build, a friend's file, a download).

1. Builder → **Add your own .elf / .bin** → type a name → **Add personal file**. Download and upload the json as in step 3.
2. Name your file `<name>_v<version>.elf`, for example `My-Tool_v1.0.elf` (`.bin` works too).
3. Put it in the repo's `payloads/` folder (web uploader is fine for one file; many files: use "From a PC").
4. Run the workflow. Your file is listed with its checksum and served from your repo.

Notes: a personal file **beats** an upstream copy with the same name. New version = upload `My-Tool_v1.1.elf`.
Only share files you may redistribute.

## Library + Store (keep notes on every repo you find)

`web/library.html` keeps two lists side by side:

| | File | Used by |
|---|---|---|
| 📚 **Library** | `data/PLUZ5-infos.json` (`.md` and `.xlsx` are built from it) | you: notes, author, variant, tags |
| 🏪 **Store** | `configs/payload_registry.json` | pldmgr: only what the PS5 downloads |

1. Add a repo link (it lands in the Library). Tick blocks, or **drag** them from Library to Store (and back to remove).
2. Every bulk action shows a count and a list before it runs. **Undo** works for the session. Nothing is hard-deleted: "Mark removed" is restorable.
3. **Copy block** (text), **Copy JSON** or **Copy Store JSON** on any selection.
4. Download both files, upload them to `data/` and `configs/`, run the workflow.

Variant = who made *that build* (`org` = original). In the Store `org` is written as `default`, so no file renames are needed.

## Other source types

| Need | Set on the card |
|---|---|
| Several files in a release | **Asset pattern**, e.g. `name-*.elf` |
| Pre-releases not tagged beta/alpha | **Tag pattern**, e.g. `v0.1.*` |
| File on a web page, not a release | **Direct file URL** + **Version** |
| Keep it listed but never fetch | `"fetch": false` (edit json) |

## P5 · P5P · P5U (hardware tag)

`P5` regular/slim PS5 only · `P5P` PS5 Pro · `P5U` universal (both) · blank = not stated (never guessed).
It describes the **console model**; FW min/max describes the **firmware**.

## Modes

| | **source** (default) | hosted |
|---|---|---|
| Repo holds | json only | the binaries in `payloads/` |
| pldmgr downloads from | the original release | your repo |
| Old builds | latest | up to 3 per payload |
| Zip-only releases | skipped | extracted |

Set `mode` in `configs/settings.json` or `PLUZ_MODE` in `.env`. In both modes, files you put in `payloads/` are used.

## From a PC (the web uploader drops hidden files and big batches)

1. Create an **empty** repo. 2. Unzip this project. 3. Edit `.env`: `GH_USER`, `GH_REPO`, portable tool folders, and a **classic** token (`repo` + `workflow`); `.env` is never uploaded.
4. Run **`PLUZ-AllStar.bat`** (Linux: `./pluz-allstar.sh`): links the folder to the repo, fetches, builds, validates, pushes. 5. Do steps 2-3 of section 1 once.

`PLUZ-AllStar.bat debug` writes a log (token hidden) to `logs/`. Stuck logins: `PLUZ-GHclean.bat`.

## Troubleshooting

| You see | Do this |
|---|---|
| Workflow red, push `403` | Section 1 step 2, re-run |
| Builder 404 | Pages not live yet: Branch must say `main`, press Save, repo Public. Or open `web/builder.html` from the unzipped folder |
| `[SKIP] N candidate assets` | Set **Asset pattern** |
| `[SKIP] no 'beta' release` | Set **Tag pattern** or Channel; the log lists real tags |
| `[SKIP] only a .zip asset` | Pick another asset, use hosted mode, or unzip and add it as your own file |
| `[SKIP] does not resolve` | A file in `payloads/` is not named `<name>_v<version>.elf` or has no registry entry |
| `could not read releases (403)` | GitHub rate limit; re-run later |
| Manifest has 0 entries | `configs/payload_registry.json` is still the empty one |
| Daily runs stopped | GitHub pauses idle repos after 60 days: press **Run workflow** once |
| AllStar: `Repository not found` | Fix `GH_USER` / `GH_REPO` in `.env` |
| pldmgr shows nothing | Open the raw link in a browser: 404 = wrong name/branch |

## Layout

```
.github/workflows/update.yml    daily + on change + manual
configs/payload_registry.json   YOUR list (the one file you edit)
core/                           engine, plain Python
manifests/                      generated (Source.json, split/, resolved.json)
payloads/                       your own files (and all files in hosted mode)
web/                            builder.html, catalog.html
examples/example-full.json      42-entry starter list
```

## Credits

Built on the work of the PS5 scene. Thank you to **itsPLK** (pldmgr and the webkit autoloader),
**notmaj0r** (ProsperoMgr, JailbreakStore), **nexgen999** (evoX-CoreOS ideas), **ps5-payload-dev**, **earthonion**,
**drakmor**, **Nazky**, **zecoxao**, the etaHEN and kstuff developers, and every author whose payloads these lists point to.
Thanks also to the community members who test, report and share links.

Designed by **Z3nT13**, built together with **Sparkz** (Claude, Anthropic).

*Powered By Z3nT13's PLUZ5*
