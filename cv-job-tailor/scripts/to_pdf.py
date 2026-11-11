#!/usr/bin/env python3
"""Convert a .docx to PDF and report its page count.

  python to_pdf.py IN.docx OUT.pdf

Tries, in order: Microsoft Word (Windows, via PowerShell COM), Microsoft Word
(Mac, via docx2pdf if installed), LibreOffice (soffice / libreoffice).
Prints PAGES=<n> at the end. Word gives the most faithful result because the
CV was designed in Word; LibreOffice may swap fonts slightly.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile


def via_word_windows(src, dst):
    if os.name != 'nt':
        return False
    ps = (
        "$w = New-Object -ComObject Word.Application; $w.Visible = $false;"
        f"$d = $w.Documents.Open('{src}', $false, $true);"
        f"$d.ExportAsFixedFormat('{dst}', 17); $d.Close($false); $w.Quit()"
    )
    r = subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                       capture_output=True, text=True)
    return r.returncode == 0 and os.path.exists(dst)


def via_docx2pdf(src, dst):
    try:
        from docx2pdf import convert
    except ImportError:
        return False
    try:
        convert(src, dst)
    except Exception:
        return False
    return os.path.exists(dst)


def via_soffice(src, dst):
    exe = shutil.which('soffice') or shutil.which('libreoffice')
    for guess in (r'C:\Program Files\LibreOffice\program\soffice.exe',
                  '/Applications/LibreOffice.app/Contents/MacOS/soffice'):
        if not exe and os.path.exists(guess):
            exe = guess
    if not exe:
        return False
    outdir = tempfile.mkdtemp()
    subprocess.run([exe, '--headless', '--convert-to', 'pdf', '--outdir', outdir, src],
                   capture_output=True, timeout=180)
    produced = os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + '.pdf')
    if os.path.exists(produced):
        shutil.move(produced, dst)
        return True
    return False


def page_count(pdf):
    try:
        import fitz
        return fitz.open(pdf).page_count
    except ImportError:
        pass
    try:
        from pypdf import PdfReader
        return len(PdfReader(pdf).pages)
    except ImportError:
        pass
    data = open(pdf, 'rb').read()
    return len(re.findall(rb'/Type\s*/Page[^s]', data))


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = (os.path.abspath(p) for p in sys.argv[1:])
    if os.path.exists(dst):
        os.remove(dst)
    for name, fn in (('Word', via_word_windows), ('Word (docx2pdf)', via_docx2pdf),
                     ('LibreOffice', via_soffice)):
        if fn(src, dst):
            print(f'Converted with {name}: {dst}')
            print(f'PAGES={page_count(dst)}')
            return
    sys.exit('ERROR: no converter found (needs Microsoft Word or LibreOffice).')


if __name__ == '__main__':
    main()
