# PLUZ5-Cust

Your own PS5 payload list, kept up to date by GitHub. **No payloads are shipped** --
you pick the repos, GitHub Actions checks them every day and writes a manifest that
[pldmgr](https://github.com/itsPLK/ps5-payload-manager) on your PS5 reads.

```
 builder.html ─► payload_registry.json ─► upload to configs/ ─► Actions: fetch → build → validate → commit
  (pick repos)                                                         │
                                         pldmgr "custom repository" ◄──┘  raw link to manifests/PLUZ-ps5-Source.json
```

---
## Quick start (about 10 minutes, browser only)

**1. Make your copy.** On this repo click **Use this template → Create a new repository**.
Name it anything (examples below use `PLUZ5Test`), choose **Public** (free GitHub Pages needs public), create.

**2. Let the workflow save its results.** In *your* repo: **Settings → Actions → General →
Workflow permissions → Read and write permissions → Save.**

**3. Turn on your web page.** **Settings → Pages.** Under *Build and deployment* set **Source: Deploy from a branch**,
then set the **Branch** dropdown to `main` (it starts on "None"), pick **/ (root)** and press **Save**.
The page is ready when Settings → Pages shows a green box "Your site is live at ..." (1-3 minutes; the
Actions tab shows a "pages build and deployment" run). Your address: `https://<your-name>.github.io/<your-repo>/`

**4. Build your list.** Open `https://<your-name>.github.io/<your-repo>/web/builder.html`
- paste repo URLs (one per line) → **Add**, or press **Load example list** to start from a full list;
- set Category, FW min/max and Hardware (P5 / P5P / P5U) on each card, fix any ⚠ notes;
- press **Download payload_registry.json**.

**5. Put it in your repo.** In your repo open the `configs` folder → **Add file → Upload files** →
drop `payload_registry.json` (same name replaces the old one) → **Commit changes**.
(One file is fine in the web uploader. Many files or hidden folders are not -- see "From a PC" below.)

**6. Run it once.** **Actions** tab → **PLUZ5 Update** → **Run workflow** → green tick after ~1 minute.
(Afterwards it runs by itself every day at 03:17 UTC and whenever you change `configs/`.)

**7. Check the result.** Your repo now has `manifests/PLUZ-ps5-Source.json` with your payloads.
Open the run's log if some entries show `[SKIP]` -- it prints why and what to set (see Troubleshooting).

**8. Add it to the PS5.** In pldmgr add a custom repository with this link
(replace the three parts; open it in a browser first, you should see JSON):
```
https://raw.githubusercontent.com/<your-name>/<your-repo>/main/manifests/PLUZ-ps5-Source.json
```

**Changing your list later:** open the builder → fill your user + repo in section 3 → **Load from my repo** →
edit → **Download** → upload to `configs/` again (steps 4-5). The workflow runs automatically.

---
## Builder without GitHub Pages
Open `web/builder.html` from your unzipped folder (double-click). Adding repos and **Download** work offline-style;
for the example list use **Open .json...** and choose `examples/example-full.json`.

---
## Modes (`mode` in `configs/settings.json`, or `PLUZ_MODE` in `.env`)
| | **source** (default) | hosted |
|---|---|---|
| Your repo holds | only json (`manifests/resolved.json` remembers each upstream file) | the binaries in `payloads/` |
| pldmgr downloads from | the original release | your repo |
| Old builds | latest only | up to 3 per payload; `keep old builds forever` honoured |
| Zip-only releases | skipped (need a direct .elf/.bin) | extracted |
| Size / licences | nothing to worry about | repo grows; you redistribute the files |

---
## From a PC (recommended for the maintainer; the web uploader drops hidden files)
Uses only your portable tools. Nothing personal is stored in the scripts -- only in `.env`.
1. Create an **empty** repo (no README). Tick **Template repository** if others should copy it.
2. Unzip this project anywhere (show hidden files).
3. Open `.env`: set `GH_USER`, `GH_REPO`, the portable folders (`PLUZ_PY_DIR`, `PLUZ_GIT_DIR`), and paste a
   **classic** token (`repo` + `workflow` scopes) after `GH_TOKEN=`. `.env` is gitignored: never uploaded.
4. Double-click **`PLUZ-AllStar.bat`** (Arch/Linux: `./pluz-allstar.sh`). It links the folder to the repo, fetches,
   builds, validates, commits and pushes. Run it any time.
5. Then do steps 2, 3 and 6 above (permissions, Pages, first workflow run).

Which repo you push to is decided by `GH_USER` / `GH_REPO` in `.env` only. Change them and run AllStar again and the folder
is re-pointed (and rebased onto that repo) automatically. The folder is never tied to the old repo.

`PLUZ-AllStar.bat debug` saves a full log (token hidden) in `logs\`. Stuck GitHub logins: `PLUZ-GHclean.bat`.

---
## Troubleshooting
| You see | Do this |
|---|---|
| Workflow red, `403` / `Permission denied` on push | Step 2 (Read and write permissions), then re-run |
| Builder page is a 404 ("There isn't a GitHub Pages site here") | Pages is not on yet: redo step 3 and make sure the Branch dropdown says `main` and you pressed Save. The repo must be Public. Wait for the green "live" box. Meanwhile you can use the builder offline (below) |
| `[SKIP] ... N candidate assets` | The release has several files. Set **Asset pattern** (e.g. `name-*.elf`) on that card |
| `[SKIP] ... no 'beta' release` | Set **Tag pattern** (e.g. `v1.*`) or change Channel; the log line `recent releases:` shows the real tags |
| `[SKIP] ... only a .zip asset` | Source mode needs a direct .elf/.bin; use hosted mode or pick another asset |
| `could not read releases (403)` | GitHub rate limit; it clears on its own. Re-run later |
| Manifest has 0 entries | `configs/payload_registry.json` is still the empty one -- repeat steps 4-5 |
| Daily runs stopped | GitHub pauses scheduled runs after 60 days without any commit. Press **Run workflow** once to wake it |
| AllStar says `Repository not found` | The repo name in `.env` (`GH_USER` / `GH_REPO`) is wrong or the repo does not exist. Fix `.env`; the script now points git at whatever `.env` says |
| pldmgr shows nothing | Open your raw link in a browser. 404 = wrong name/branch; empty list = see row above |

## Layout
```
.github/workflows/update.yml   daily + on change + manual
configs/payload_registry.json  YOUR list (the one file you edit)   categories.json  settings.json
core/                          engine (plain Python, no installs)
manifests/                     generated: Source.json, split/, resolved.json (Hosted.json in hosted mode)
payloads/                      only used in hosted mode
web/                           builder.html (make/edit your list + your links), catalog.html (browse)
examples/example-full.json     47-entry starter list
PLUZ-AllStar.bat / pluz-allstar.sh   full local run          PLUZ-GHclean.bat / pluz-ghclean.sh   clean logins/repo
pluz.py                        python pluz.py <check|fetch|update|validate|cleanup|dedupe>
```
Hardware tags: `P5` regular/slim · `P5P` Pro · `P5U` both. Versions come from the release tag; `fw_min`/`fw_max`
are typed by you, blank means unknown. You are responsible for the licences of anything you host.
