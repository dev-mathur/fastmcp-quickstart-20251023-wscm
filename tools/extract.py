#!/usr/bin/env python3
"""Extract a book (PDF or EPUB) into clean, chapter-split markdown.

Usage:
    python tools/extract.py BOOK.pdf --out work/my-book
    python tools/extract.py BOOK.epub --out work/my-book

Writes:
    <out>/chapters/NN-slug.md   one file per chapter
    <out>/manifest.json         title, author, backend, chapters, word counts, warnings, skipped sections

Exit codes:
    0  extracted, possibly with warnings (read manifest.json)
    2  bad input or missing dependency
    3  scanned PDF with no text layer; run ocrmypdf first, then re-run
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from posixpath import dirname as posix_dirname, join as posix_join, normpath as posix_normpath
from urllib.parse import unquote
from xml.etree import ElementTree as ET

MIN_CHAPTER_WORDS = 200
WORDS_PER_PAGE = (180, 450)  # sanity band for total words vs. page count

# Sections that are not part of the book's argument. They are skipped and reported, not deleted silently.
SKIP_TITLE = re.compile(
    r"^(copyright|title page|half[- ]title|contents|table of contents|dedication|epigraph|"
    r"acknowledg|about the author|also by|praise for|index|bibliography|further reading|"
    r"permissions|colophon|cover|newsletter|sign up|excerpt from)",
    re.IGNORECASE,
)

CHAPTER_LINE = re.compile(
    r"^\s*(?:#{1,3}\s*)?(?:\*\*)?(?P<label>(?:chapter|part|book|section)\s+(?:\d+|[ivxlc]+)\b[^\n]*|"
    r"prologue\b[^\n]*|epilogue\b[^\n]*|introduction\b[^\n]*|preface\b[^\n]*|conclusion\b[^\n]*|afterword\b[^\n]*)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------- helpers


def slugify(text: str, fallback: str = "section") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:48].strip("-") or fallback


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'’-]+\b", text))


def clean_text(text: str) -> str:
    """Fix common extraction damage without changing the author's words."""
    text = text.replace("­", "")  # soft hyphens
    for lig, plain in {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}.items():
        text = text.replace(lig, plain)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)  # join words hyphenated across lines
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _edge_lines(page: str, zone: int = 2) -> set[int]:
    """Indexes of the first and last few non-empty lines of a page, where running headers and footers live."""
    indexes = [i for i, ln in enumerate(page.splitlines()) if ln.strip()]
    return set(indexes[:zone] + indexes[-zone:])


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("#") or bool(CHAPTER_LINE.match(stripped))


def strip_running_lines(pages: list[str]) -> list[str]:
    """Remove short header/footer lines that repeat on many pages, plus bare page numbers.

    Only the top and bottom lines of a page are candidates, and headings are never removed,
    so a "Chapter 3" line is safe even though "Chapter #" repeats once per chapter.
    """
    if len(pages) < 6:
        return pages
    counts: Counter[str] = Counter()
    for page in pages:
        lines = page.splitlines()
        seen = {
            re.sub(r"\d+", "#", lines[i].strip())
            for i in _edge_lines(page)
            if 0 < len(lines[i].strip()) < 70 and not _is_heading(lines[i])
        }
        counts.update(seen)
    threshold = max(4, int(len(pages) * 0.3))
    repeated = {line for line, n in counts.items() if n >= threshold}
    cleaned = []
    for page in pages:
        lines = page.splitlines()
        edges = _edge_lines(page)
        keep = []
        for i, line in enumerate(lines):
            if i in edges and not _is_heading(line):
                normal = re.sub(r"\d+", "#", line.strip())
                if normal in repeated or re.fullmatch(r"\s*(page\s+)?\d{1,4}\s*", line, re.IGNORECASE):
                    continue
            keep.append(line)
        cleaned.append("\n".join(keep))
    return cleaned


# ---------------------------------------------------------------- PDF


def have(command: str) -> bool:
    return shutil.which(command) is not None


def pdf_triage(path: Path):
    try:
        import fitz  # PyMuPDF
    except ImportError:
        sys.exit("PyMuPDF is required for PDFs: pip install pymupdf pymupdf4llm")
    doc = fitz.open(path)
    sample = [doc[i].get_text() for i in range(min(len(doc), 25))]
    chars_per_page = sum(len(s.strip()) for s in sample) / max(len(sample), 1)
    return doc, chars_per_page


def pdf_page_texts(doc, path: Path, backend: str) -> tuple[list[str], str]:
    """Return one markdown/text string per page and the backend actually used."""
    if backend in ("auto", "pymupdf4llm"):
        try:
            import pymupdf4llm

            chunks = pymupdf4llm.to_markdown(doc, page_chunks=True, show_progress=False)
            return [c["text"] for c in chunks], "pymupdf4llm"
        except ImportError:
            if backend == "pymupdf4llm":
                sys.exit("pymupdf4llm is not installed: pip install pymupdf4llm")
        except Exception as exc:  # noqa: BLE001 - fall through to the next backend
            print(f"pymupdf4llm failed ({exc}); trying another backend", file=sys.stderr)

    if backend in ("auto", "pdftotext") and have("pdftotext"):
        out = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, check=True
        ).stdout
        return out.split("\f"), "pdftotext"

    if backend == "docling":
        try:
            from docling.document_converter import DocumentConverter

            markdown = DocumentConverter().convert(str(path)).document.export_to_markdown()
            return [markdown], "docling"  # no per-page split; chapter detection falls back to headings
        except ImportError:
            sys.exit("docling is not installed: pip install docling")

    if backend == "marker" and have("marker_single"):
        out_dir = path.parent / f".marker-{path.stem}"
        subprocess.run(["marker_single", str(path), "--output_dir", str(out_dir)], check=True)
        md = next(out_dir.rglob("*.md")).read_text(encoding="utf-8")
        return [md], "marker"

    # Last resort: plain PyMuPDF text
    return [page.get_text() for page in doc], "pymupdf"


def split_pdf_by_toc(doc, pages: list[str]) -> list[dict] | None:
    """Use the PDF's own bookmarks. Prefer the shallowest level that yields chapter-sized sections."""
    toc = doc.get_toc(simple=True)
    if len(toc) < 3 or len(pages) != len(doc):
        return None
    for level in (1, 2):
        entries = [(title, page) for lvl, title, page in toc if lvl == level and page >= 1]
        if len(entries) >= 3:
            break
    else:
        return None
    sections = []
    for index, (title, start) in enumerate(entries):
        end = entries[index + 1][1] - 1 if index + 1 < len(entries) else len(pages)
        end = max(end, start)
        sections.append(
            {
                "title": title.strip(),
                "start_page": start,
                "end_page": end,
                "text": "\n\n".join(pages[start - 1 : end]),
            }
        )
    return sections


def split_by_headings(text: str) -> list[dict]:
    """Fallback: split on lines that look like 'Chapter 3', 'Part II', 'Introduction', or markdown headings."""
    lines = text.splitlines()
    starts = []
    for i, line in enumerate(lines):
        m = CHAPTER_LINE.match(line)
        if m and len(line.strip()) < 120:
            starts.append((i, m.group("label").strip(" #*")))
        elif re.match(r"^#{1,2}\s+\S", line) and len(line.strip()) < 100:
            starts.append((i, line.lstrip("# ").strip()))
    # Collapse headings that sit directly under one another ("Chapter 3" then "The Title")
    merged: list[tuple[int, str]] = []
    for i, label in starts:
        if merged and i - merged[-1][0] <= 3:
            merged[-1] = (merged[-1][0], f"{merged[-1][1]}: {label}")
        else:
            merged.append((i, label))
    if len(merged) < 3:
        return [{"title": "Full text", "start_page": None, "end_page": None, "text": text}]
    sections = []
    for index, (start, label) in enumerate(merged):
        end = merged[index + 1][0] if index + 1 < len(merged) else len(lines)
        sections.append({"title": label, "start_page": None, "end_page": None, "text": "\n".join(lines[start:end])})
    return sections


def extract_pdf(path: Path, backend: str):
    doc, chars_per_page = pdf_triage(path)
    meta = doc.metadata or {}
    if chars_per_page < 50:
        print(
            f"This PDF has almost no text layer ({chars_per_page:.0f} characters per page). "
            "It looks scanned. Run:\n"
            f'  ocrmypdf --skip-text "{path}" "{path.with_suffix(".ocr.pdf")}"\n'
            "then re-run this script on the .ocr.pdf file.",
            file=sys.stderr,
        )
        sys.exit(3)
    pages, used = pdf_page_texts(doc, path, backend)
    page_count = len(doc)
    pages = strip_running_lines(pages)
    sections = split_pdf_by_toc(doc, pages) if len(pages) == page_count else None
    split_by = "pdf-bookmarks"
    if sections is None:
        sections = split_by_headings("\n\n".join(pages))
        split_by = "headings"
    info = {
        "title": (meta.get("title") or "").strip(),
        "author": (meta.get("author") or "").strip(),
        "format": "pdf",
        "pages": page_count,
        "backend": used,
        "split_by": split_by,
        "chars_per_page": round(chars_per_page),
    }
    return info, sections


# ---------------------------------------------------------------- EPUB


class TextExtractor(HTMLParser):
    """Turn XHTML into light markdown: headings keep their level, paragraphs are separated by blank lines."""

    BLOCK = {"p", "div", "li", "blockquote", "br", "tr", "section", "article"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.heading: int | None = None
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav"):
            self.skip += 1
        elif re.fullmatch(r"h[1-6]", tag):
            self.parts.append("\n\n" + "#" * int(tag[1]) + " ")
            self.heading = int(tag[1])
        elif tag in self.BLOCK:
            self.parts.append("\n\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav"):
            self.skip = max(0, self.skip - 1)
        elif re.fullmatch(r"h[1-6]", tag):
            self.parts.append("\n\n")
            self.heading = None
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(re.sub(r"\s+", " ", data) if self.heading else data)

    def text(self) -> str:
        return re.sub(r"[ \t]+", " ", "".join(self.parts))


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def extract_epub(path: Path):
    with zipfile.ZipFile(path) as z:
        container = ET.fromstring(z.read("META-INF/container.xml"))
        opf_path = next(e.attrib["full-path"] for e in container.iter() if local(e.tag) == "rootfile")
        opf = ET.fromstring(z.read(opf_path))
        base = posix_dirname(opf_path)

        manifest = {e.attrib["id"]: e.attrib for e in opf.iter() if local(e.tag) == "item"}
        spine = [e.attrib["idref"] for e in opf.iter() if local(e.tag) == "itemref"]
        title = next((e.text for e in opf.iter() if local(e.tag) == "title" and e.text), "")
        author = next((e.text for e in opf.iter() if local(e.tag) == "creator" and e.text), "")

        # Titles from the table of contents (EPUB3 nav or EPUB2 NCX), keyed by file name
        toc_titles: dict[str, str] = {}
        nav_item = next((m for m in manifest.values() if "nav" in m.get("properties", "")), None)
        ncx_item = next((m for m in manifest.values() if m.get("media-type") == "application/x-dtbncx+xml"), None)
        try:
            if nav_item:
                html = z.read(posix_normpath(posix_join(base, nav_item["href"]))).decode("utf-8", "ignore")
                for href, label in re.findall(r'<a[^>]+href="([^"#]+)[^"]*"[^>]*>(.*?)</a>', html, re.S):
                    toc_titles.setdefault(unquote(href).split("/")[-1], re.sub(r"<[^>]+>|\s+", " ", label).strip())
            elif ncx_item:
                ncx = ET.fromstring(z.read(posix_normpath(posix_join(base, ncx_item["href"]))))
                for point in ncx.iter():
                    if local(point.tag) == "navPoint":
                        label = next((t.text for t in point.iter() if local(t.tag) == "text" and t.text), "")
                        src = next((c.attrib["src"] for c in point if local(c.tag) == "content"), "")
                        toc_titles.setdefault(unquote(src.split("#")[0]).split("/")[-1], label.strip())
        except (KeyError, ET.ParseError):
            pass

        sections = []
        for idref in spine:
            item = manifest.get(idref)
            if not item or "html" not in item.get("media-type", ""):
                continue
            href = unquote(item["href"])
            parser = TextExtractor()
            parser.feed(z.read(posix_normpath(posix_join(base, href))).decode("utf-8", "ignore"))
            text = parser.text()
            heading = re.search(r"^#{1,3}\s+(.+)$", text, re.M)
            label = toc_titles.get(href.split("/")[-1]) or (heading.group(1).strip() if heading else Path(href).stem)
            sections.append({"title": label, "start_page": None, "end_page": None, "text": text})

    info = {"title": title, "author": author, "format": "epub", "pages": None, "backend": "zipfile+html.parser", "split_by": "epub-spine"}
    return info, sections


# ---------------------------------------------------------------- shared pipeline


def merge_tiny(sections: list[dict]) -> list[dict]:
    """Fold sections under 60 words (part dividers, one-line pages) into the next section."""
    merged: list[dict] = []
    carry = None
    for section in sections:
        if carry:
            section = {**section, "text": carry["text"] + "\n\n" + section["text"], "title": section["title"]}
            carry = None
        if count_words(section["text"]) < 60 and not SKIP_TITLE.match(section["title"]):
            carry = section
            continue
        merged.append(section)
    if carry and merged:
        merged[-1]["text"] += "\n\n" + carry["text"]
    return merged


def garble_report(text: str) -> list[str]:
    issues = []
    letters = sum(c.isalpha() for c in text)
    if text and letters / len(text) < 0.6:
        issues.append("low share of letters (tables, code, or OCR noise?)")
    if text.count("�") > 3:
        issues.append(f"{text.count(chr(0xFFFD))} replacement characters")
    if re.search(r"\b\w{25,}\b", text):
        issues.append("very long run-together words (missing spaces?)")
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("book", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="output directory, e.g. work/my-book")
    parser.add_argument("--backend", default="auto", choices=["auto", "pymupdf4llm", "pdftotext", "docling", "marker"])
    parser.add_argument("--min-words", type=int, default=MIN_CHAPTER_WORDS)
    args = parser.parse_args()

    if not args.book.exists():
        sys.exit(f"File not found: {args.book}")
    suffix = args.book.suffix.lower()
    if suffix == ".pdf":
        info, sections = extract_pdf(args.book, args.backend)
    elif suffix == ".epub":
        info, sections = extract_epub(args.book)
    else:
        sys.exit("Only .pdf and .epub files are supported")

    warnings: list[str] = []
    skipped: list[dict] = []
    kept: list[dict] = []
    for section in merge_tiny(sections):
        section["text"] = clean_text(section["text"])
        words = count_words(section["text"])
        if SKIP_TITLE.match(section["title"].strip()):
            skipped.append({"title": section["title"], "words": words, "reason": "front or back matter"})
        elif words == 0:
            skipped.append({"title": section["title"], "words": 0, "reason": "empty"})
        else:
            kept.append(section)

    if not kept:
        sys.exit("No chapter text found. Try --backend docling or --backend marker, or OCR the file first.")

    chapters_dir = args.out / "chapters"
    if chapters_dir.exists():
        shutil.rmtree(chapters_dir)
    chapters_dir.mkdir(parents=True)

    chapters = []
    for n, section in enumerate(kept, start=1):
        words = count_words(section["text"])
        slug = slugify(section["title"], f"chapter-{n}")
        filename = f"{n:02d}-{slug}.md"
        (chapters_dir / filename).write_text(f"# {section['title']}\n\n{section['text']}\n", encoding="utf-8")
        if words < args.min_words:
            warnings.append(f"chapter {n} ({section['title']!r}) has only {words} words; may be an extraction failure")
        for issue in garble_report(section["text"]):
            warnings.append(f"chapter {n} ({section['title']!r}): {issue}")
        chapters.append(
            {
                "n": n,
                "title": section["title"],
                "file": f"chapters/{filename}",
                "words": words,
                "start_page": section["start_page"],
                "end_page": section["end_page"],
            }
        )

    total_words = sum(c["words"] for c in chapters)
    if info["pages"]:
        per_page = total_words / info["pages"]
        low, high = WORDS_PER_PAGE
        if not low <= per_page <= high:
            warnings.append(
                f"{per_page:.0f} words per page is outside the usual {low}-{high} band; "
                "text may be missing (images, tables) or doubled"
            )
    if len(chapters) == 1:
        warnings.append("only one section was found; chapter boundaries could not be detected")

    manifest = {
        **info,
        "title": info["title"] or args.book.stem,
        "source_file": args.book.name,
        "total_words": total_words,
        "chapter_count": len(chapters),
        "chapters": chapters,
        "skipped": skipped,
        "warnings": warnings,
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"{manifest['title']}: {len(chapters)} chapters, {total_words:,} words ({info['backend']}, split by {info['split_by']})")
    for message in warnings:
        print(f"  warning: {message}")
    if skipped:
        print(f"  skipped {len(skipped)} section(s): " + ", ".join(s["title"] for s in skipped[:6]))
    print(f"Wrote {args.out / 'manifest.json'}")


if __name__ == "__main__":
    main()
