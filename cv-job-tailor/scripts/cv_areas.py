#!/usr/bin/env python3
"""Read and edit the yellow "dynamic areas" of a CV .docx.

The CV the candidate received from Nir marks every area that may be re-tuned
per job (title, keyword line, summary phrases, "Focused on" lists, skills...)
with a yellow highlight. This script works ONLY on those areas, so the fixed
skeleton (names, companies, dates, achievements, metrics) is never touched.

Commands
  python cv_areas.py show  CV.docx
      Prints every paragraph. Highlighted groups appear as [[H<n>: text]] and
      get an id like P12.H0. Also prints the id list with text lengths.

  python cv_areas.py apply CV.docx changes.json OUT_EDIT.docx OUT_CLEAN.docx
      changes.json = {"P12.H0": "new text", ...}
      OUT_EDIT  : same document, new text, yellow kept on all dynamic areas
      OUT_CLEAN : same document, new text, every highlight removed (for PDF)
      Prints a length report (old vs new chars) so growth is visible.

Only the standard library is used, so it runs anywhere Python 3 runs.
"""
import json
import re
import sys
import zipfile

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
PARA_RE = re.compile(r'<w:p[ >].*?</w:p>', re.S)
RUN_RE = re.compile(r'<w:r[ >].*?</w:r>', re.S)
TEXT_RE = re.compile(r'<w:t(?: [^>]*)?>(.*?)</w:t>|<w:t(?: [^>]*)?/>|<w:tab/>|<w:br/>', re.S)
HL_RE = re.compile(r'<w:highlight w:val="(?!none)[^"]+"\s*/>')
SHD_RE = re.compile(r'<w:shd [^>]*w:fill="(FFFF00|ffff00|yellow)"[^>]*/>')


def unescape(s):
    return (s.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
             .replace('&apos;', "'").replace('&amp;', '&'))


def escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def run_text(r):
    out = []
    for m in TEXT_RE.finditer(r):
        tok = m.group(0)
        if tok.startswith('<w:tab'):
            out.append('\t')
        elif tok.startswith('<w:br'):
            out.append('\n')
        elif m.group(1) is not None:
            out.append(unescape(m.group(1)))
    return ''.join(out)


def run_is_hl(r):
    rpr = re.search(r'<w:rPr>.*?</w:rPr>', r, re.S)
    if not rpr:
        return False
    return bool(HL_RE.search(rpr.group(0)) or SHD_RE.search(rpr.group(0)))


def load(path):
    with zipfile.ZipFile(path) as z:
        return z.read('word/document.xml').decode('utf-8')


def paragraphs(xml):
    """Yield (pidx, span, runs) where runs = [(span_in_para, text, is_hl)]."""
    for pidx, pm in enumerate(PARA_RE.finditer(xml)):
        p = pm.group(0)
        runs = [(rm.span(), run_text(rm.group(0)), run_is_hl(rm.group(0)))
                for rm in RUN_RE.finditer(p)]
        yield pidx, pm.span(), p, runs


def groups(runs):
    """Contiguous highlighted runs (ignoring empty runs) -> list of run-index lists."""
    out, cur = [], []
    for i, (_, text, hl) in enumerate(runs):
        if hl:
            cur.append(i)
        elif text == '':
            continue
        else:
            if cur:
                out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def cmd_show(path):
    xml = load(path)
    ids = []
    for pidx, _, _, runs in paragraphs(xml):
        gs = groups(runs)
        in_group = {i: g for g, idxs in enumerate(gs) for i in idxs}
        parts, printed = [], set()
        for i, (_, text, hl) in enumerate(runs):
            if i in in_group:
                g = in_group[i]
                if g in printed:
                    continue
                printed.add(g)
                gtext = ''.join(runs[j][1] for j in gs[g])
                parts.append(f'[[H{g}: {gtext}]]')
                ids.append((f'P{pidx}.H{g}', gtext))
            else:
                parts.append(text)
        line = ''.join(parts)
        if line.strip():
            print(f'P{pidx}: {line}')
    print('\n=== DYNAMIC AREAS ===')
    if not ids:
        print('NONE FOUND - this file has no yellow highlights.')
    for i, t in ids:
        print(f'{i} ({len(t)} chars): {t}')


def set_run_text(r, text):
    """Replace all text content of a run with `text` (keeps its rPr)."""
    rpr = re.search(r'<w:rPr>.*?</w:rPr>', r, re.S)
    head = re.match(r'<w:r(?: [^>]*)?>', r).group(0)
    body = f'<w:t xml:space="preserve">{escape(text)}</w:t>' if text else ''
    return head + (rpr.group(0) if rpr else '') + body + '</w:r>'


def strip_hl(xml):
    xml = HL_RE.sub('', xml)
    return SHD_RE.sub('', xml)


def cmd_apply(path, changes_path, out_edit, out_clean):
    with open(changes_path, encoding='utf-8') as f:
        changes = json.load(f)
    xml = load(path)
    new_parts, last, seen = [], 0, set()
    report = []
    for pidx, (ps, pe), p, runs in paragraphs(xml):
        gs = groups(runs)
        edits = {}
        for g, idxs in enumerate(gs):
            key = f'P{pidx}.H{g}'
            if key in changes:
                seen.add(key)
                old = ''.join(runs[j][1] for j in idxs)
                new = changes[key]
                report.append((key, old, new))
                edits[idxs[0]] = new
                for j in idxs[1:]:
                    edits[j] = ''
        if not edits:
            continue
        # rebuild paragraph with edited runs
        out, plast = [], 0
        for i, ((rs, re_), _, _) in enumerate(runs):
            if i in edits:
                out.append(p[plast:rs])
                out.append(set_run_text(p[rs:re_], edits[i]))
                plast = re_
        out.append(p[plast:])
        new_parts.append(xml[last:ps])
        new_parts.append(''.join(out))
        last = pe
    new_parts.append(xml[last:])
    new_xml = ''.join(new_parts)

    unknown = set(changes) - seen
    if unknown:
        sys.exit(f'ERROR: unknown area ids {sorted(unknown)} - run "show" again.')

    for out_path, doc_xml in ((out_edit, new_xml), (out_clean, strip_hl(new_xml))):
        with zipfile.ZipFile(path) as zin, zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == 'word/document.xml':
                    data = doc_xml.encode('utf-8')
                zout.writestr(item, data)

    print('=== CHANGES ===')
    total = 0
    for key, old, new in report:
        d = len(new) - len(old)
        total += d
        flag = '  <-- grew a lot, check line wrap' if d > 15 else ''
        print(f'{key}: {len(old)} -> {len(new)} chars ({d:+d}){flag}')
        print(f'   OLD: {old}\n   NEW: {new}')
    print(f'TOTAL length change: {total:+d} chars')
    print(f'Wrote {out_edit}\nWrote {out_clean}')


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == 'show':
        cmd_show(a[1])
    elif len(a) == 5 and a[0] == 'apply':
        cmd_apply(*a[1:])
    else:
        sys.exit(__doc__)
