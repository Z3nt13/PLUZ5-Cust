"""pluz infos -- the Library (every source you know about) and its readable copies.

data/PLUZ5-infos.json   master (edited with web/library.html)
data/PLUZ5-infos.md     generated, same blocks as a readable list
data/PLUZ5-infos.xlsx   generated, one row per entry (filter / group by Author, Variant ...)

  python pluz.py infos                  rebuild the .md and .xlsx from the json
  python pluz.py infos --import f.md    add blocks from a markdown list (new ids are added)
  python pluz.py infos --sync-store     add a Library entry for every Store entry that has none
  python pluz.py infos --check          validate only

The Library is never used by pldmgr. Only configs/payload_registry.json (the Store) is.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pluz_common import repo_root, load_config, Log  # noqa: E402

POWERED = "Powered By Z3nT13's PLUZ5"
FIELDS = ["URL", "Author", "Variant", "Desc", "Tags", "Notes", "Status"]


def slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-") or "entry"


def norm_url(u: str) -> str:
    return re.sub(r"(\.git)?/*$", "", str(u or "").strip().lower())


def owner_of(url: str) -> str:
    m = re.match(r"https?://github\.com/([^/]+)/", str(url or ""), re.I)
    return m.group(1) if m else ""


def make_id(name: str, variant: str) -> str:
    return f"{slug(name)}-{slug(variant or 'org')}"


def load_infos(path: Path) -> dict:
    if path.exists():
        d = json.loads(path.read_text(encoding="utf-8"))
        d.setdefault("entries", [])
        return d
    return {"schema_version": 1, "comment": "Your Library. Edit with web/library.html.", "entries": []}


def save_infos(path: Path, d: dict) -> None:
    out = {k: v for k, v in d.items() if k not in ("entries", "powered_by")}
    out["entries"] = d["entries"]
    out["powered_by"] = POWERED
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------- markdown <-> entries ----------
def parse_md(text: str) -> list[dict]:
    entries, section, cur = [], "General", None
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            cur = None
        elif line.startswith("### "):
            raw = line[4:].strip()
            cur = {"name": re.sub(r"\s+\([^()]*\)$", "", raw) or raw, "section": section, "_f": {}}
            entries.append(cur)
        elif cur is not None:
            m = re.match(r"-\s+\*\*(\w+):\*\*\s*(.*)$", line)
            if m and m.group(1) in FIELDS:
                cur["_f"][m.group(1)] = m.group(2).strip()
    out = []
    for e in entries:
        f = e.pop("_f")
        url = f.get("URL", "")
        url = url if url.startswith("http") else ""
        variant = f.get("Variant") or "org"
        out.append({
            "id": make_id(e["name"], variant), "name": e["name"], "url": url,
            "author": f.get("Author") or owner_of(url), "variant": variant, "section": e["section"],
            "desc": f.get("Desc", ""), "tags": [t.lstrip("#") for t in f.get("Tags", "").split() if t.startswith("#")],
            "notes": f.get("Notes", ""), "removed": f.get("Status", "").lower() == "removed", "hidden": False})
    return out


def to_md(d: dict) -> str:
    lines = ["# PLUZ5 Library", "", f"_{POWERED}. Generated from `PLUZ5-infos.json`; edit it with `web/library.html`._", ""]
    sections: dict[str, list] = {}
    for e in d["entries"]:
        sections.setdefault(e.get("section") or "General", []).append(e)
    for sec, items in sections.items():
        lines += [f"## {sec}", ""]
        for e in items:
            lines.append(f"### {e['name']}")
            lines.append(f"- **URL:** {e.get('url') or '(none)'}")
            lines.append(f"- **Author:** {e.get('author') or ''}")
            lines.append(f"- **Variant:** {e.get('variant') or 'org'}")
            lines.append(f"- **Desc:** {e.get('desc') or ''}")
            lines.append("- **Tags:** " + " ".join("#" + t for t in e.get("tags", [])))
            lines.append(f"- **Notes:** {e.get('notes') or ''}")
            if e.get("removed"):
                lines.append("- **Status:** removed")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# ---------- xlsx (stdlib only) ----------
def _col(i: int) -> str:
    return "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i]


def _esc(s) -> str:
    s = str(s if s is not None else "")
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def to_xlsx(d: dict, path: Path) -> None:
    head = ["Name", "Variant", "Author", "Section", "URL", "Tags", "Desc", "Notes", "Status", "Id"]
    rows = [head]
    for e in d["entries"]:
        rows.append([e.get("name"), e.get("variant"), e.get("author"), e.get("section"), e.get("url"),
                     " ".join("#" + t for t in e.get("tags", [])), e.get("desc"), e.get("notes"),
                     "removed" if e.get("removed") else "", e.get("id")])
    sheet = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
             '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>',
             '<cols>' + "".join(f'<col min="{i+1}" max="{i+1}" width="{w}" customWidth="1"/>'
                                for i, w in enumerate([28, 12, 18, 26, 48, 40, 60, 60, 10, 30])) + '</cols>',
             '<sheetData>']
    for r, row in enumerate(rows, 1):
        cells = "".join(f'<c r="{_col(c)}{r}" t="inlineStr"{" s=\"1\"" if r == 1 else ""}><is><t xml:space="preserve">{_esc(v)}</t></is></c>'
                        for c, v in enumerate(row))
        sheet.append(f'<row r="{r}">{cells}</row>')
    sheet.append('</sheetData>')
    sheet.append(f'<autoFilter ref="A1:J{len(rows)}"/></worksheet>')
    styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
              '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
              '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
              '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
              '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
              '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
              '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs></styleSheet>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Library" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                   '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr("xl/styles.xml", styles)
        z.writestr("xl/worksheets/sheet1.xml", "".join(sheet))


# ---------- library <-> store ----------
def merge_entries(d: dict, new: list[dict]) -> int:
    have = {e["id"] for e in d["entries"]}
    n = 0
    for e in new:
        if e["id"] in have:
            continue
        d["entries"].append(e)
        have.add(e["id"])
        n += 1
    return n


def sync_store(d: dict, registry: dict) -> int:
    urls = {norm_url(e.get("url")) for e in d["entries"] if e.get("url")}
    new = []
    for ident, ent in registry.get("payloads", {}).items():
        for var, r in ent.get("variants", {}).items():
            u = r.get("source_repo") or ""
            if not str(u).startswith("http") or norm_url(u) in urls:
                continue
            urls.add(norm_url(u))
            variant = "org" if var == "default" else var
            name = re.sub(r"\s+\([^()]*\)$", "", r.get("display_name") or ident) or ident
            eid, n = make_id(name, variant), 2
            taken = {x["id"] for x in d["entries"] + new}
            while eid in taken:
                eid, n = f"{make_id(name, variant)}-{n}", n + 1
            new.append({"id": eid, "name": name, "url": u,
                        "author": r.get("author") or owner_of(u), "variant": variant, "section": "From the Store",
                        "desc": "", "tags": ["payload"], "notes": r.get("note") or "", "removed": False, "hidden": False})
    return merge_entries(d, new)


def check(d: dict, log: Log) -> bool:
    ok, seen = True, set()
    for e in d["entries"]:
        if e.get("id") in seen:
            log.line(f"[FAIL] duplicate library id {e.get('id')}")
            ok = False
        seen.add(e.get("id"))
        if not e.get("name"):
            log.line(f"[FAIL] entry {e.get('id')} has no name")
            ok = False
        if e.get("url") and not str(e["url"]).startswith("https://"):
            log.line(f"[FAIL] {e['id']}: url must start with https://")
            ok = False
    if ok:
        log.line(f"[OK  ] library: {len(d['entries'])} entries, ids unique")
    return ok


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="pluz infos")
    ap.add_argument("--import", dest="imp", help="markdown file with ### blocks to add")
    ap.add_argument("--sync-store", action="store_true", help="add Library entries for Store entries that have none")
    ap.add_argument("--check", action="store_true", help="validate only, write nothing")
    a = ap.parse_args(argv)
    root = repo_root()
    cfg = load_config(root)
    dp = root / "data" / "PLUZ5-infos.json"
    d = load_infos(dp)
    with Log(root, "pluz_infos") as log:
        if a.check:
            return 0 if check(d, log) else 1
        if a.imp:
            n = merge_entries(d, parse_md(Path(a.imp).read_text(encoding="utf-8")))
            log.line(f"imported {n} new entr{'y' if n == 1 else 'ies'} from {a.imp}")
        if a.sync_store:
            n = sync_store(d, cfg["registry"])
            log.line(f"added {n} Library entr{'y' if n == 1 else 'ies'} from the Store")
        if not check(d, log):
            return 1
        save_infos(dp, d)
        (root / "data" / "PLUZ5-infos.md").write_text(to_md(d), encoding="utf-8")
        to_xlsx(d, root / "data" / "PLUZ5-infos.xlsx")
        log.line("wrote data/PLUZ5-infos.json, .md, .xlsx")
    return 0


if __name__ == "__main__":
    sys.exit(main())
