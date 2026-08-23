#!/usr/bin/env python3
"""
Download, execute, and export all ThinkStats 3e notebooks to a single
interleaved PDF: preface, then chapter + solutions, then examples.
"""

import copy
import os
import re
import subprocess
import sys
import shutil
import urllib.request
from concurrent.futures import ThreadPoolExecutor, Future
from pathlib import Path

BASE_RAW = "https://raw.githubusercontent.com/AllenDowney/ThinkStats/v3/nb"
SOLN_RAW = "https://raw.githubusercontent.com/AllenDowney/ThinkStats/v3/soln"
DATA_RAW = "https://raw.githubusercontent.com/AllenDowney/ThinkStats/v3/data"

# Notebooks with no paired solutions
PREFACE = ["jupyter_intro"]

# (chapter stem, solutions stem) — solutions mirror the chapter name
CHAPTERS = [
    ("chap01", "chap01"), ("chap02", "chap02"), ("chap03", "chap03"),
    ("chap04", "chap04"), ("chap05", "chap05"), ("chap06", "chap06"),
    ("chap07", "chap07"), ("chap08", "chap08"), ("chap09", "chap09"),
    ("chap10", "chap10"), ("chap11", "chap11"), ("chap12", "chap12"),
    ("chap13", "chap13"), ("chap14", "chap14"),
]

EXAMPLES: list[str] = []

OUT_DIR        = Path(__file__).parent / "chapters"
COMMENTARY_DIR = Path(__file__).parent / "commentary"
BOOK_PDF       = Path(__file__).parent / "thinkstats3.pdf"
SOLN_PDF       = Path(__file__).parent / "thinkstats3_solutions.pdf"
TITLE_PAGE     = OUT_DIR / "_title.pdf"
SOLN_TITLE_PAGE = OUT_DIR / "_soln_title.pdf"

CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
]

PRINT_CSS = """
<style>
/* ── Page breaks ─────────────────────────────────────────────────────────── */
pre, .highlight, .jp-InputArea, .jp-OutputArea, .cell,
.input_area, .output_area { break-inside: avoid; }

/* ── Hide Jupyter chrome, anchors, and stderr/warning outputs ────────────── */
.jp-InputPrompt, .jp-OutputPrompt,
.input_prompt, .output_prompt,
.prompt, div.prompt,
.out_prompt_overlay,
#notebook-container .prompt,
.celltoolbar, .ctb_globalshow,
.jp-Toolbar, #menubar, #header,
.navbar, .nav,
a.anchor-link, .anchor-link,
.jp-OutputArea-output[data-mime-type="application/vnd.jupyter.stderr"],
.output_stderr { display: none !important; }

/* ── Page & content layout ───────────────────────────────────────────────── */
body { background: #fff; margin: 0; padding: 0; }
#notebook-container, .jp-Notebook, .container {
  max-width: 100% !important; width: 100% !important;
  padding: 0 !important; box-shadow: none !important;
}

/* ── Typography ──────────────────────────────────────────────────────────── */
body, p, li, td, th, blockquote,
.jp-RenderedHTMLCommon,
.jp-RenderedHTMLCommon p,
.text_cell_render {
  font-family: Georgia, 'Times New Roman', serif !important;
  font-size: 11.5pt !important;
  line-height: 1.38 !important;
  color: #1c1c1c !important;
}

/* ── Links ───────────────────────────────────────────────────────────────── */
a { color: #1c1c1c !important; text-decoration: none !important; }

/* ── Headings ────────────────────────────────────────────────────────────── */
h1, h2, h3, h4 { font-family: Georgia, serif !important; color: #111 !important; }
h1 {
  font-size: 20pt !important; font-weight: 700;
  margin: 2em 0 0.5em !important;
  padding-bottom: 0.3em;
  border-bottom: 2px solid #ddd;
}
h2 { font-size: 14pt !important; font-weight: 700; margin: 1.6em 0 0.4em !important; }
h3 { font-size: 12pt !important; font-weight: 700; margin: 1.3em 0 0.3em !important; }

/* ── Paragraphs ──────────────────────────────────────────────────────────── */
p, .jp-RenderedHTMLCommon p, .text_cell_render p {
  text-align: justify !important;
  hyphens: auto !important;
  margin: 0 0 0.75em !important;
}

/* ── Code ────────────────────────────────────────────────────────────────── */
pre, code, kbd, samp,
.jp-InputArea pre, .highlight pre {
  font-family: 'SF Mono', Menlo, Monaco, 'Courier New', monospace !important;
  font-size: 9pt !important;
  line-height: 1.4 !important;
  color: #1c1c1c !important;
}
div.highlight, .jp-InputArea .highlight {
  background: #f6f6f6 !important;
  border: none !important;
  border-left: 3px solid #5b8dd9 !important;
  border-radius: 0 3px 3px 0 !important;
  padding: 0.85em 1em 0.85em 1.1em !important;
  margin: 0.3em 0 !important;
}

/* ── Output ──────────────────────────────────────────────────────────────── */
.jp-OutputArea-output pre, .output_text pre, .output_subarea pre {
  background: #fafafa !important;
  border-left: 3px solid #d0d0d0 !important;
  padding: 0.55em 1em !important;
  font-size: 8.5pt !important;
  color: #333 !important;
  border-radius: 0 3px 3px 0 !important;
}

/* ── Tables ──────────────────────────────────────────────────────────────── */
table {
  border-collapse: collapse !important;
  margin: 0.4em 0 !important;
  font-family: 'SF Mono', Menlo, Monaco, monospace !important;
  font-size: 7.5pt !important;
  width: auto !important;
}
th {
  background: #2e5fa3 !important;
  color: #fff !important;
  padding: 2px 7px !important;
  font-weight: 600 !important;
  text-align: left !important;
}
td {
  padding: 1px 7px !important;
  border-bottom: 1px solid #e0e0e0 !important;
  color: #1c1c1c !important;
  text-align: left !important;
}
tr:nth-child(even) td { background: #f2f5fb !important; }
.split-table-label {
  font-family: Georgia, serif; font-size: 7.5pt; color: #888;
  text-align: left; margin: 6px 0 2px; font-style: italic;
}

/* ── Images ──────────────────────────────────────────────────────────────── */
img, svg { max-width: 88% !important; height: auto; display: block; margin: 1em auto; }

/* ── Blockquotes ─────────────────────────────────────────────────────────── */
blockquote {
  border-left: 3px solid #5b8dd9 !important;
  margin: 1em 0 !important;
  padding: 0.4em 1em !important;
  color: #3a3a3a !important;
  font-style: italic !important;
  background: #f5f7fc !important;
}

/* ── Commentary blocks (injected after each exercise) ────────────────────── */
.commentary-block {
  background: #f0f4fb;
  border-left: 4px solid #2e5fa3;
  border-radius: 0 4px 4px 0;
  padding: 0.7em 1em 0.7em 1.1em;
  margin: 0.8em 0 1.2em;
  break-inside: avoid;
}
.commentary-banner {
  font-family: -apple-system, Helvetica, sans-serif !important;
  font-size: 8pt !important; font-weight: 700; letter-spacing: 0.1em;
  text-transform: uppercase; color: #2e5fa3; margin-bottom: 0.4em;
}
.commentary-block p {
  font-size: 10.5pt !important; line-height: 1.45 !important;
  margin: 0 0 0.4em !important; color: #222 !important;
}
.commentary-block code {
  font-size: 8.5pt !important; background: #e4ecf7 !important;
  padding: 1px 3px; border-radius: 2px;
}
.commentary-block ul, .commentary-block ol {
  margin: 0.2em 0 0.4em 1.2em; font-size: 10.5pt !important;
}
</style>
</head>"""

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

PREFETCH: dict[str, list[tuple[str, str]]] = {}


# ── helpers ───────────────────────────────────────────────────────────────────

def download(url: str, dest: Path, retries: int = 3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
            with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as f:
                f.write(resp.read())
            return
        except Exception as e:
            if attempt == retries - 1:
                raise
            print(f"  download retry {attempt + 1}/{retries} for {dest.name}: {e}", flush=True)


def find_chrome() -> str | None:
    for p in CHROME_PATHS:
        if p and Path(p).exists():
            return p
    return None


def execute_to_html(nb_path: Path, html_path: Path, work_dir: Path):
    result = subprocess.run(
        [
            sys.executable, "-m", "nbconvert",
            "--to", "html",
            "--execute",
            "--ExecutePreprocessor.timeout=600",
            "--ExecutePreprocessor.kernel_name=python3",
            "--output", str(html_path.resolve()),
            str(nb_path.resolve()),
        ],
        cwd=str(work_dir.resolve()),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:])


def title_from_html(html_path: Path) -> str:
    text = html_path.read_text(encoding="utf-8")
    m = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.DOTALL)
    if not m:
        return html_path.stem
    return re.sub(r'<[^>]+>', '', m.group(1)).replace('¶', '').strip()


def patch_html(src: Path, dst: Path):
    """Apply print CSS to src (raw nbconvert output), write result to dst."""
    text = src.read_text(encoding="utf-8")
    dst.write_text(text.replace("</head>", PRINT_CSS, 1), encoding="utf-8")


def strip_stderr_outputs(html_path: Path):
    """Remove stderr/warning output cells so they don't appear in the PDF."""
    from bs4 import BeautifulSoup
    html = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    removed = 0
    # New nbconvert format
    for div in soup.find_all("div", attrs={"data-mime-type": "application/vnd.jupyter.stderr"}):
        div.decompose()
        removed += 1
    # Old nbconvert format
    for div in soup.find_all("div", class_="output_stderr"):
        div.decompose()
        removed += 1
    if removed:
        html_path.write_text(str(soup), encoding="utf-8")


_PAGE_WIDTH_PT = 490   # A4 minus 15mm margins each side
_CHAR_PT       = 4.3   # per char at 7.5pt monospace
_COL_PAD_PT    = 16    # padding per column


def _table_width_pt(table) -> float:
    col_max: dict[int, int] = {}
    for row in table.find_all("tr"):
        for i, cell in enumerate(row.find_all(["th", "td"])):
            col_max[i] = max(col_max.get(i, 0), len(cell.get_text(strip=True)))
    return sum(n * _CHAR_PT + _COL_PAD_PT for n in col_max.values())


def split_wide_tables(html_path: Path):
    from bs4 import BeautifulSoup
    html = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    changed = False
    for table in soup.find_all("table"):
        thead = table.find("thead")
        tbody = table.find("tbody")
        if not thead or not tbody:
            continue
        header_rows = thead.find_all("tr")
        if not header_rows:
            continue
        header_cells = header_rows[-1].find_all(["th", "td"])
        n_cols = len(header_cells)
        body_rows = tbody.find_all("tr")
        if not body_rows:
            continue
        n_index = len(body_rows[0].find_all("th"))
        n_data = n_cols - n_index

        if _table_width_pt(table) <= _PAGE_WIDTH_PT:
            continue

        all_col_max: dict[int, int] = {}
        for row in table.find_all("tr"):
            for i, cell in enumerate(row.find_all(["th", "td"])):
                all_col_max[i] = max(all_col_max.get(i, 0), len(cell.get_text(strip=True)))
        index_width = sum(all_col_max.get(i, 4) * _CHAR_PT + _COL_PAD_PT for i in range(n_index))
        data_col_widths = [all_col_max.get(n_index + i, 4) * _CHAR_PT + _COL_PAD_PT
                           for i in range(n_data)]
        groups: list[list[int]] = []
        cur_group: list[int] = []
        cur_w = index_width
        for rel_i, col_w in enumerate(data_col_widths):
            if cur_group and cur_w + col_w > _PAGE_WIDTH_PT:
                groups.append(cur_group)
                cur_group = []
                cur_w = index_width
            cur_group.append(n_index + rel_i)
            cur_w += col_w
        if cur_group:
            groups.append(cur_group)

        if len(groups) <= 1:
            continue

        wrapper = soup.new_tag("div")
        for g_num, group in enumerate(groups, 1):
            lbl = soup.new_tag("div", attrs={"class": "split-table-label"})
            lbl.string = f"(part {g_num} of {len(groups)})"
            wrapper.append(lbl)
            wrapper.append(_build_sub_table(table, list(range(n_index)) + group, soup))
        table.replace_with(wrapper)
        changed = True
    if changed:
        html_path.write_text(str(soup), encoding="utf-8")


def _build_sub_table(original, col_indices, soup):
    new_table = soup.new_tag("table")
    for sec in ("thead", "tfoot"):
        section = original.find(sec)
        if section:
            new_sec = soup.new_tag(sec)
            for row in section.find_all("tr"):
                cells = row.find_all(["th", "td"])
                new_row = soup.new_tag("tr")
                for i in col_indices:
                    if i < len(cells):
                        new_row.append(copy.copy(cells[i]))
                new_sec.append(new_row)
            new_table.append(new_sec)
    tbody = original.find("tbody")
    if tbody:
        new_tbody = soup.new_tag("tbody")
        for row in tbody.find_all("tr"):
            cells = row.find_all(["th", "td"])
            new_row = soup.new_tag("tr")
            for i in col_indices:
                if i < len(cells):
                    new_row.append(copy.copy(cells[i]))
            new_tbody.append(new_row)
        new_table.append(new_tbody)
    return new_table


def _norm(text: str) -> list[str]:
    return re.sub(r'[^a-z0-9\s]', ' ', text.lower()).split()


_STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'of', 'for', 'in', 'is', 'to',
    'with', 'exercise', 'exercises', 'problem', 'solution',
    'at', 'on', 'by', 'up', 'it', 'do', 'as', 'so', 'if', 'we', 'be',
    'but', 'not', 'no', 'my', 'us', 'vs', 'via',
}


def _heading_keywords(heading_words: list[str]) -> set[str]:
    return {w for w in heading_words if len(w) > 1 and w not in _STOPWORDS}


def _fuzzy_hit(word: str, text_words: set[str]) -> bool:
    if word in text_words:
        return True
    prefix = word[:5]
    for w in text_words:
        if len(w) < 4:
            continue
        if w[:5] == prefix:
            return True
        if len(word) >= 4 and w[:len(word)] == word:
            return True
    return False


def _precision(exercise_words: list[str], heading_words: list[str]) -> float:
    hw = _heading_keywords(heading_words)
    if not hw:
        return 0.0
    ew = set(exercise_words)
    return sum(1 for w in hw if _fuzzy_hit(w, ew)) / len(hw)


def _cell_ancestor(tag) -> object:
    el = tag
    for _ in range(12):
        p = el.parent
        if p is None or p.name in ('main', 'body', '[document]'):
            return el
        cls = ' '.join(p.get('class') or [])
        if 'jp-Cell' in cls and 'jp-Cell-inputWrapper' not in cls and 'jp-Cell-inputArea' not in cls:
            return p
        el = p
    return el


def _exercise_match_text(para) -> str:
    """Return text for matching: full cell text, extended into following cells when short."""
    cell = _cell_ancestor(para)
    text = cell.get_text()
    if len(text) >= 200:
        return text[:800]
    for sib in cell.find_next_siblings():
        sib_cls = ' '.join(sib.get('class') or [])
        if 'jp-MarkdownCell' in sib_cls:
            if any(p.get_text(strip=True).lower().startswith('exercise')
                   and len(p.get_text(strip=True)) > 20
                   for p in sib.find_all('p')):
                break
            text += ' ' + sib.get_text()
        elif 'jp-CodeCell' in sib_cls:
            text += ' ' + sib.get_text()
            break
        if len(text) >= 800:
            break
    return text[:800]


def _make_block(content: str, soup, md_lib) -> object:
    com_html = md_lib.markdown(content, extensions=["fenced_code", "tables"])
    from bs4 import BeautifulSoup as BS
    return BS(
        f'<div class="commentary-block">'
        f'<div class="commentary-banner">Commentary</div>'
        f'{com_html}</div>',
        "html.parser"
    )


def _is_exercise_h3(tag) -> bool:
    return (tag.name == 'h3'
            and tag.get_text(strip=True).replace('¶', '').strip().lower().startswith('exercise'))


def inject_commentary(html_path: Path, md_path: Path):
    if not md_path.exists():
        return

    from bs4 import BeautifulSoup
    import markdown as md_lib

    raw = md_path.read_text(encoding="utf-8")
    sections: list[tuple[list[str], str]] = []
    cur_hw: list[str] | None = None
    cur_lines: list[str] = []

    for line in raw.split('\n'):
        if line.startswith('## '):
            if cur_hw is not None:
                sections.append((cur_hw, '\n'.join(cur_lines).strip()))
            cur_hw = _norm(line[3:])
            cur_lines = []
        elif line.startswith('# '):
            pass
        else:
            cur_lines.append(line)
    if cur_hw is not None:
        sections.append((cur_hw, '\n'.join(cur_lines).strip()))

    if not sections:
        return

    ex_sections = [(mw, c) for mw, c in sections if 'exercise' in mw]

    html = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    injected = 0

    # ── Detect notebook format ────────────────────────────────────────────────
    # stats3: exercises marked by <h3> headings inside markdown cells
    # bayes2: exercises marked by <p> tags starting with "exercise"
    ex_h3s = [h for h in soup.find_all('h3') if _is_exercise_h3(h)]

    if ex_h3s:
        # ── stats3 format ─────────────────────────────────────────────────────
        # Each exercise is a markdown cell containing an h3 + description text.
        # Use the full cell text for matching, insert before the next exercise cell.
        ex_cells = [(_cell_ancestor(h3), _cell_ancestor(h3).get_text()[:800]) for h3 in ex_h3s]

        # Build full score matrix, then greedy bipartite match (highest score first).
        # This prevents a section from blocking a better match elsewhere when it ties.
        all_scores: list[tuple[float, int, int]] = []
        for sec_idx, (mw, sec_content) in enumerate(ex_sections):
            hw = _heading_keywords(mw)
            if not hw:
                continue
            for ex_idx, (cell, cell_text) in enumerate(ex_cells):
                s = _precision(_norm(cell_text), mw)
                if s >= 0.10:
                    all_scores.append((s, sec_idx, ex_idx))
        all_scores.sort(reverse=True)

        assigned_secs: set[int] = set()
        assigned_exs:  set[int] = set()
        matches: dict[int, str] = {}
        for score, sec_idx, ex_idx in all_scores:
            if sec_idx in assigned_secs or ex_idx in assigned_exs:
                continue
            matches[ex_idx] = ex_sections[sec_idx][1]
            assigned_secs.add(sec_idx)
            assigned_exs.add(ex_idx)

        for idx in sorted(matches):
            cell, _ = ex_cells[idx]
            insert_before = None
            for sib in cell.find_next_siblings():
                if any(_is_exercise_h3(h) for h in sib.find_all('h3')):
                    insert_before = sib
                    break
            block = _make_block(matches[idx], soup, md_lib)
            if insert_before:
                insert_before.insert_before(block)
            else:
                insert_after = cell
                for sib in cell.find_next_siblings():
                    sib_cls = ' '.join(sib.get('class') or [])
                    if 'jp-CodeCell' in sib_cls:
                        insert_after = sib
                    elif 'jp-MarkdownCell' in sib_cls:
                        if any(_is_exercise_h3(h) for h in sib.find_all('h3')):
                            break
                    else:
                        break
                insert_after.insert_after(block)
            injected += 1

    else:
        # ── bayes2 format ─────────────────────────────────────────────────────
        ex_paras = [p for p in soup.find_all('p')
                    if p.get_text(strip=True).lower().startswith('exercise')
                    and len(p.get_text(strip=True)) > 20]

        if not ex_paras or not ex_sections:
            return

        all_scores: list[tuple[float, int, int]] = []
        for sec_idx, (mw, _) in enumerate(ex_sections):
            hw = _heading_keywords(mw)
            if not hw:
                continue
            for para_idx, para in enumerate(ex_paras):
                s = _precision(_norm(_exercise_match_text(para)), mw)
                if s >= 0.15:
                    all_scores.append((s, sec_idx, para_idx))
        all_scores.sort(reverse=True)

        assigned_secs: set[int] = set()
        assigned_exs:  set[int] = set()
        matches: dict[int, str] = {}
        for score, sec_idx, para_idx in all_scores:
            if sec_idx in assigned_secs or para_idx in assigned_exs:
                continue
            matches[para_idx] = ex_sections[sec_idx][1]
            assigned_secs.add(sec_idx)
            assigned_exs.add(para_idx)

        for para_idx in sorted(matches):
            para = ex_paras[para_idx]
            cell = _cell_ancestor(para)
            insert_before = None
            for sibling in cell.find_next_siblings():
                for p2 in sibling.find_all('p'):
                    t = p2.get_text(strip=True)
                    if t.lower().startswith('exercise') and len(t) > 20:
                        insert_before = sibling
                        break
                if insert_before:
                    break
            block = _make_block(matches[para_idx], soup, md_lib)
            if insert_before:
                insert_before.insert_before(block)
            else:
                insert_after = cell
                for sib in cell.find_next_siblings():
                    sib_cls = ' '.join(sib.get('class') or [])
                    if 'jp-CodeCell' in sib_cls:
                        insert_after = sib
                    elif 'jp-MarkdownCell' in sib_cls:
                        if any(p.get_text(strip=True).lower().startswith('exercise')
                               and len(p.get_text(strip=True)) > 20
                               for p in sib.find_all('p')):
                            break
                    else:
                        break
                insert_after.insert_after(block)
            injected += 1

    if injected > 0:
        html_path.write_text(str(soup), encoding="utf-8")
        print(f"  injected {injected} commentary blocks", flush=True)


def verify_chapter(raw_html: Path, html_path: Path, key: str):
    """Hard assertions after all HTML transformations.

    1. No code cells lost vs raw.
    2. Every exercise has a commentary block (soln_ chapters only).
    3. Commentary always comes after solution code, never before it.
    """
    from bs4 import BeautifulSoup

    def _count_cls(path: Path, cls: str) -> int:
        soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
        return len([d for d in soup.find_all('div') if cls in ' '.join(d.get('class') or [])])

    raw_code = _count_cls(raw_html,  'jp-CodeCell')
    pat_code = _count_cls(html_path, 'jp-CodeCell')
    if raw_code != pat_code:
        raise AssertionError(
            f"{key}: CONTENT LOST — raw has {raw_code} code cells, patched has {pat_code}"
        )

    if not key.startswith('soln_'):
        return

    soup = BeautifulSoup(html_path.read_text(encoding='utf-8'), 'html.parser')

    # Detect exercise format
    ex_h3s = [h for h in soup.find_all('h3') if _is_exercise_h3(h)]
    if ex_h3s:
        n_ex = len(ex_h3s)
    else:
        n_ex = len([p for p in soup.find_all('p')
                    if p.get_text(strip=True).lower().startswith('exercise')
                    and len(p.get_text(strip=True)) > 20])

    n_com = len(soup.find_all('div', class_='commentary-block'))
    if n_com != n_ex:
        raise AssertionError(
            f"{key}: COMMENTARY MISSING — {n_ex} exercises but {n_com} commentary blocks"
        )

    # Ordering: EX…[CODE*]…COM — COM must not appear before solution code
    main = soup.find('main') or soup.find('body')
    events: list[str] = []
    for tag in (main or soup).descendants:
        if ex_h3s:
            if _is_exercise_h3(tag):
                events.append('EX')
        else:
            if tag.name == 'p':
                t = tag.get_text(strip=True)
                if t.lower().startswith('exercise') and len(t) > 20:
                    events.append('EX')
        if tag.name == 'div':
            cls = ' '.join(tag.get('class') or [])
            if 'commentary-block' in cls:
                events.append('COM')
            elif 'jp-CodeCell' in cls:
                events.append('CODE')

    ex_count = com_count = 0
    com_seen = code_after_com = False
    for ev in events:
        if ev == 'EX':
            if com_count < ex_count:
                raise AssertionError(
                    f"{key}: ORDER WRONG — exercise #{ex_count+1} has no commentary before next exercise"
                )
            if code_after_com:
                raise AssertionError(
                    f"{key}: PLACEMENT WRONG — commentary #{com_count} appears before solution code"
                )
            ex_count += 1
            com_seen = False
            code_after_com = False
        elif ev == 'CODE':
            if com_seen:
                code_after_com = True
        else:
            com_seen = True
            com_count += 1
    if ex_count > 0 and com_count < ex_count:
        raise AssertionError(f"{key}: ORDER WRONG — last exercise has no commentary")
    if code_after_com:
        raise AssertionError(f"{key}: PLACEMENT WRONG — last commentary appears before solution code")


def header_template(label: str) -> str:
    return (
        '<div style="font-family: -apple-system, Helvetica, sans-serif; '
        'font-size: 9px; width: 100%; padding: 0 15mm; box-sizing: border-box; '
        'display: flex; justify-content: space-between; color: #888;">'
        f'<span>{label}</span>'
        '<span><span class="pageNumber"></span></span>'
        '</div>'
    )


def html_to_pdf(html_path: Path, pdf_path: Path, chrome: str, header: str = ""):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=chrome)
        page = browser.new_page()
        page.goto(html_path.resolve().as_uri())
        page.wait_for_load_state("networkidle")
        page.evaluate("""async () => {
            if (window.MathJax && MathJax.typesetPromise) {
                await MathJax.typesetPromise();
            }
        }""")
        page.pdf(
            path=str(pdf_path),
            format="A4",
            margin={"top": "20mm", "bottom": "15mm",
                    "left": "15mm", "right": "15mm"},
            print_background=True,
            display_header_footer=True,
            header_template=header_template(header) if header else "<span></span>",
            footer_template="<span></span>",
        )
        browser.close()


def make_divider_page(chrome: str, label: str, title: str, out_pdf: Path):
    html = out_pdf.with_suffix(".html")
    html.write_text(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: Georgia, 'Times New Roman', serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    background: #fff;
    color: #111;
    text-align: center;
  }}
  .rule {{ width: 80px; height: 3px; background: #2e5fa3; margin: 0 auto 28px; }}
  .label {{
    font-size: 11pt;
    font-weight: 400;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #2e5fa3;
    margin-bottom: 18px;
  }}
  .title {{
    font-size: 28pt;
    font-weight: 700;
    line-height: 1.25;
    max-width: 75%;
    color: #111;
  }}
</style>
</head>
<body>
  <div class="rule"></div>
  <div class="label">{label}</div>
  <div class="title">{title}</div>
</body>
</html>
""", encoding="utf-8")
    html_to_pdf(html, out_pdf, chrome)


def make_title_page(chrome: str, path: Path, note: str):
    html = path.with_suffix(".html")
    html.write_text(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: Georgia, 'Times New Roman', serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    text-align: center;
    color: #222;
    background: #fff;
  }}
  .subtitle  {{ font-size: 18px; color: #555; margin-top: 12px; }}
  .title     {{ font-size: 42px; font-weight: 700; margin-top: 8px; }}
  .edition   {{ font-size: 16px; color: #888; margin-top: 8px; }}
  .author    {{ font-size: 22px; margin-top: 48px; }}
  .note      {{ font-size: 13px; color: #888; margin-top: 8px; font-style: italic; }}
  .divider   {{ width: 60px; height: 3px; background: #ddd; margin: 40px auto; }}
  .license   {{ font-size: 12px; color: #aaa; max-width: 400px; line-height: 1.6; }}
</style>
</head>
<body>
  <div class="subtitle">Exploratory Data Analysis in Python</div>
  <div class="title">Think Stats</div>
  <div class="edition">Third Edition</div>
  <div class="author">Allen B. Downey</div>
  <div class="note">{note}</div>
  <div class="divider"></div>
  <div class="license">
    Original work by Allen Downey.<br>
    Source: <em>github.com/AllenDowney/ThinkStats</em><br>
    Licensed under CC BY-NC-SA 4.0
  </div>
</body>
</html>
""", encoding="utf-8")
    html_to_pdf(html, path, chrome)


def merge_pdfs(pdf_paths: list[Path], out: Path):
    from pypdf import PdfWriter
    writer = PdfWriter()
    for p in pdf_paths:
        writer.append(str(p))
    with open(out, "wb") as f:
        writer.write(f)


def process_notebook(key: str, nb_url: str, nb_path: Path,
                     raw_html: Path, html_path: Path, pdf_path: Path,
                     chrome: str, header_prefix: str = "",
                     commentary_md: Path | None = None) -> Path | None:
    """
    Cache layers:
      raw_html  — nbconvert output; delete to re-execute
      pdf_path  — rendered PDF; delete to re-render (CSS/commentary changes)
    html_path is always rebuilt from raw_html on every run.
    """
    # ── step 1: ensure raw HTML exists ───────────────────────────────────────
    if raw_html.exists():
        print(f"  {key}: html cached", flush=True)
    elif html_path.exists():
        # Migration: existing .html (pre-raw-cache era) becomes the raw source
        shutil.copy2(html_path, raw_html)
        print(f"  {key}: migrated existing html → raw", flush=True)
    else:
        print(f"  {key}: downloading ...", flush=True)
        try:
            download(nb_url, nb_path)
        except Exception as e:
            print(f"  {key}: FAILED (download): {e}", flush=True)
            return None

        for url, fname in PREFETCH.get(key, []):
            dest = OUT_DIR / fname
            if not dest.exists():
                try:
                    download(url, dest)
                except Exception as e:
                    print(f"  {key}: WARN prefetch {fname}: {e}", flush=True)

        print(f"  {key}: executing ...", flush=True)
        try:
            execute_to_html(nb_path, raw_html, OUT_DIR)
        except Exception as e:
            print(f"  {key}: FAILED (execute):\n{str(e)[:2000]}", flush=True)
            return None

    # ── step 2: always rebuild html from raw (picks up CSS + commentary edits) ─
    patch_html(raw_html, html_path)
    strip_stderr_outputs(html_path)
    split_wide_tables(html_path)
    if commentary_md is not None:
        inject_commentary(html_path, commentary_md)
    verify_chapter(raw_html, html_path, key)

    # ── step 3: HTML → PDF ────────────────────────────────────────────────────
    # Cache is valid only while raw HTML is older than the PDF.
    if pdf_path.exists() and pdf_path.stat().st_mtime >= raw_html.stat().st_mtime:
        print(f"  {key}: pdf cached", flush=True)
        return pdf_path

    title  = title_from_html(html_path)
    header = f"{header_prefix}{title}" if header_prefix else title

    print(f"  {key}: → PDF ...", flush=True)
    try:
        html_to_pdf(html_path, pdf_path, chrome, header=header)
        print(f"  {key}: done", flush=True)
        return pdf_path
    except Exception as e:
        print(f"  {key}: FAILED (pdf): {e}", flush=True)
        return None


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    chrome = find_chrome()
    if not chrome:
        print("ERROR: Chrome not found.")
        sys.exit(1)

    workers = min(os.cpu_count() or 4, 8)
    print(f"Using Chrome: {chrome}")
    print(f"Parallel workers: {workers}\n")

    OUT_DIR.mkdir(exist_ok=True)
    COMMENTARY_DIR.mkdir(exist_ok=True)

    print("Generating title pages ...")
    make_title_page(chrome, TITLE_PAGE, "With executed code and charts")
    make_title_page(chrome, SOLN_TITLE_PAGE, "Solutions Manual with commentary")

    original_pdfs: list[Path] = [TITLE_PAGE]
    solution_pdfs: list[Path] = [SOLN_TITLE_PAGE]
    failed: list[str] = []

    all_tasks: list[tuple[str, str, str | None]] = []

    for stem in PREFACE:
        all_tasks.append((stem, f"{BASE_RAW}/{stem}.ipynb", None))

    for chap, soln in CHAPTERS:
        all_tasks.append((chap, f"{BASE_RAW}/{chap}.ipynb", f"{SOLN_RAW}/{soln}.ipynb"))

    for stem in EXAMPLES:
        all_tasks.append((stem, f"{BASE_RAW}/{stem}.ipynb", None))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures: list[tuple[Future, Future | None, str, str | None]] = []

        for key, nb_url, soln_url in all_tasks:
            cf = pool.submit(
                process_notebook, key, nb_url,
                OUT_DIR / f"{key}.ipynb",
                OUT_DIR / f"{key}_raw.html",
                OUT_DIR / f"{key}.html",
                OUT_DIR / f"{key}.pdf",
                chrome, "",
                None,
            )
            sf = None
            if soln_url:
                skey = f"soln_{key}"
                sf = pool.submit(
                    process_notebook, skey, soln_url,
                    OUT_DIR / f"{skey}.ipynb",
                    OUT_DIR / f"{skey}_raw.html",
                    OUT_DIR / f"{skey}.html",
                    OUT_DIR / f"{skey}.pdf",
                    chrome, "Solutions — ",
                    COMMENTARY_DIR / f"{skey}.md",
                )
            futures.append((cf, sf, key, soln_url))

        for cf, sf, key, soln_url in futures:
            chap_result = cf.result()
            if chap_result:
                ch_html = OUT_DIR / f"{key}.html"
                num_m   = re.search(r'\d+', key)
                label   = f"Chapter {num_m.group()}" if num_m else key.replace("_", " ").title()
                div_pdf = OUT_DIR / f"{key}_divider.pdf"
                make_divider_page(chrome, label, title_from_html(ch_html), div_pdf)
                original_pdfs += [div_pdf, chap_result]
            else:
                failed.append(key)

            if sf is not None:
                soln_result = sf.result()
                skey = f"soln_{key}"
                if soln_result:
                    sl_html  = OUT_DIR / f"{skey}.html"
                    num_m    = re.search(r'\d+', key)
                    slabel   = f"Solutions — Chapter {num_m.group()}" if num_m else f"Solutions — {key}"
                    sdiv_pdf = OUT_DIR / f"{skey}_divider.pdf"
                    make_divider_page(chrome, slabel, title_from_html(sl_html), sdiv_pdf)
                    solution_pdfs += [sdiv_pdf, soln_result]
                else:
                    failed.append(skey)

    if len(original_pdfs) <= 1 and len(solution_pdfs) <= 1:
        print("\nNothing succeeded.")
        sys.exit(1)

    print(f"\nMerging original ({len(original_pdfs)} parts) → {BOOK_PDF.name} ...")
    merge_pdfs(original_pdfs, BOOK_PDF)
    print(f"Merging solutions ({len(solution_pdfs)} parts) → {SOLN_PDF.name} ...")
    merge_pdfs(solution_pdfs, SOLN_PDF)
    print(f"\nDone!\n  {BOOK_PDF.resolve()}\n  {SOLN_PDF.resolve()}")

    if failed:
        print(f"\nFailed (skipped): {', '.join(failed)}")


if __name__ == "__main__":
    main()
