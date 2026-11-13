"""Build the PDF of the accession agreement from its Markdown.

    python agreements/build_pdf.py            # writes agreements/accession-agreement.pdf
    python agreements/build_pdf.py --check    # fails if the committed PDF is out of date

accession-agreement.md is the text; the PDF is what the legal representative of an
organisation downloads from the onboarding portal, fills in, signs and uploads. Change the
Markdown, run this script and commit both files.

Only a small part of Markdown is understood, enough for the agreement:

- ``#``, ``##`` and ``###`` headings, paragraphs, ``- `` lists, ``**bold**``, links;
- ``- [ ] label``: a checkbox the signer ticks;
- a two-column table whose header row is empty (``| | |``): one row per field to fill in,
  label on the left; the row ``Signature`` is left as an empty box for the signature.

Every PDF carries in its footer a short hash of the Markdown it was built from, so a signed
copy says exactly which text was signed. The build is reproducible: the same Markdown
gives the same bytes (reportlab in invariant mode, version in requirements.txt).
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    CondPageBreak,
    Flowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "accession-agreement.md"
TARGET = HERE / "accession-agreement.pdf"

SITE = "https://citcomai-hub.github.io"
REPO = "https://github.com/CitComAI-Hub/citcom-ds-rulebook"
# Relative links of the Markdown → where a reader of the PDF finds them
PAGES = {"../rulebook/README.md": f"{SITE}/rulebook/rules/"}

INK = colors.HexColor("#1a1a1a")
MUTED = colors.HexColor("#5c5c5c")
RULE = colors.HexColor("#9a9a9a")
FIELD_BG = colors.HexColor("#f2f4f7")

BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13.5,
                      textColor=INK, alignment=TA_LEFT, spaceAfter=5)
TITLE = ParagraphStyle("title", parent=BODY, fontName="Helvetica-Bold", fontSize=16,
                       leading=20, spaceAfter=8)
H2 = ParagraphStyle("h2", parent=BODY, fontName="Helvetica-Bold", fontSize=11,
                    leading=14, spaceBefore=10, spaceAfter=5)
H3 = ParagraphStyle("h3", parent=BODY, fontName="Helvetica-Bold", fontSize=9.5,
                    spaceBefore=6, spaceAfter=2)
LABEL = ParagraphStyle("label", parent=BODY, spaceAfter=0, textColor=MUTED)
CHECK_LABEL = ParagraphStyle("check", parent=BODY, spaceAfter=0)

FIELD_H = 6.5 * mm
SIGNATURE_H = 28 * mm
MARGIN = 22 * mm
TEXT_W = A4[0] - 2 * MARGIN
LABEL_W = 55 * mm


def link_target(url: str) -> str:
    page, _, anchor = url.partition("#")
    if page in PAGES:
        return PAGES[page] + (f"#{anchor}" if anchor else "")
    return url


def inline(text: str) -> str:
    """Markdown inline → reportlab paragraph markup."""
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"&lt;(https?://[^&\s]+)&gt;",
                  lambda m: f'<link href="{m[1]}" color="#1f4e99">{m[1]}</link>', text)
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
                  lambda m: f'<link href="{link_target(m[2])}" color="#1f4e99">{m[1]}</link>',
                  text)


def field_name(label: str, used: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    name, n = base, 2
    while name in used:
        name, n = f"{base}_{n}", n + 1
    used.add(name)
    return name


class TextField(Flowable):
    """A fillable text box of the PDF form."""

    def __init__(self, name: str, label: str, height: float = FIELD_H):
        super().__init__()
        self.name, self.label, self.height = name, label, height

    def wrap(self, avail_width, avail_height):
        self.width = avail_width
        return self.width, self.height

    def draw(self):
        self.canv.acroForm.textfield(
            name=self.name, tooltip=self.label, x=0, y=0, width=self.width,
            height=self.height, fontName="Helvetica", fontSize=9.5, borderWidth=0.6,
            borderColor=RULE, fillColor=FIELD_BG, textColor=INK, relative=True)


class SignatureBox(Flowable):
    """An empty box for a handwritten or electronic signature."""

    def wrap(self, avail_width, avail_height):
        self.width = avail_width
        return self.width, SIGNATURE_H

    def draw(self):
        self.canv.setStrokeColor(RULE)
        self.canv.setLineWidth(0.6)
        self.canv.rect(0, 0, self.width, SIGNATURE_H)


class CheckBox(Flowable):
    def __init__(self, name: str, label: str):
        super().__init__()
        self.name, self.label = name, label

    def wrap(self, avail_width, avail_height):
        return 4 * mm, 4 * mm

    def draw(self):
        self.canv.acroForm.checkbox(
            name=self.name, tooltip=self.label, x=0, y=-0.6 * mm, size=3.8 * mm,
            borderWidth=0.6, borderColor=RULE, fillColor=FIELD_BG, buttonStyle="check",
            textColor=INK, relative=True)


def form_table(rows: list[str], used: set[str]) -> Table:
    data, style = [], [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), 4 * mm),
        ("RIGHTPADDING", (1, 0), (1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ]
    for i, label in enumerate(rows):
        if label.lower() == "signature":
            data.append([Paragraph(escape(label), LABEL), SignatureBox()])
            style.append(("VALIGN", (0, i), (0, i), "TOP"))
        else:
            data.append([Paragraph(escape(label), LABEL), TextField(field_name(label, used), label)])
    return Table(data, colWidths=[LABEL_W, TEXT_W - LABEL_W], style=TableStyle(style), hAlign="LEFT")


def checkbox_list(items: list[str], used: set[str]) -> Table:
    data = [[CheckBox(field_name(item.split(":")[0], used), item), Paragraph(inline(item), CHECK_LABEL)]
            for item in items]
    return Table(data, colWidths=[7 * mm, TEXT_W - 7 * mm], hAlign="LEFT", style=TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))


def bullet_list(items: list[str]) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(inline(i), ParagraphStyle("li", parent=BODY, spaceAfter=2)),
                  leftIndent=5 * mm, value="–") for i in items],
        bulletType="bullet", start="–", leftIndent=5 * mm, bulletFontSize=9.5,
        spaceAfter=5)


def parse(markdown: str, used: set[str]) -> list[Flowable]:
    """The subset of Markdown described in the module docstring → flowables."""
    lines = markdown.splitlines()
    story: list[Flowable] = []
    pending_heading: list[Flowable] = []

    def add(flow):
        # A heading stays on the same page as what follows it
        if pending_heading:
            story.append(KeepTogether([*pending_heading, flow]))
            pending_heading.clear()
        else:
            story.append(flow)

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.startswith("#"):
            level, text = len(line) - len(line.lstrip("#")), line.lstrip("#").strip()
            style = {1: TITLE, 2: H2}.get(level, H3)
            pending_heading.append(Paragraph(inline(text), style))
            i += 1
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if any(cells) and not set("".join(cells)) <= set("-: "):
                    rows.append(cells[0])
                i += 1
            add(form_table(rows, used))
            add(Spacer(0, 3 * mm))
        elif re.match(r"- \[ \] ", line):
            items = []
            while i < len(lines) and re.match(r"- \[ \] ", lines[i]):
                items.append(lines[i][6:].strip())
                i += 1
            add(checkbox_list(items, used))
            add(Spacer(0, 2 * mm))
        elif line.startswith("- "):
            items = []
            while i < len(lines) and (lines[i].startswith("- ") or lines[i].startswith("  ")):
                if lines[i].startswith("- "):
                    items.append(lines[i][2:].strip())
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            add(bullet_list(items))
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not re.match(r"[#|]|- ", lines[i]):
                para.append(lines[i].strip())
                i += 1
            add(Paragraph(inline(" ".join(para)), BODY))
    story.extend(pending_heading)
    return story


def keep_sections(markdown: str) -> list[Flowable]:
    """Every ``##`` section with fields to fill in starts a new page if it does not fit."""
    sections, current = [], []
    for line in markdown.splitlines():
        if line.startswith("## ") and current:
            sections.append("\n".join(current))
            current = []
        current.append(line)
    sections.append("\n".join(current))
    used: set[str] = set()
    story: list[Flowable] = []
    for section in sections:
        rows = len(re.findall(r"^(\| \S|- \[ \] )", section, re.M))
        if rows:
            # Start a new page unless the whole section fits in what is left of this one
            signature = SIGNATURE_H if re.search(r"^\| Signature \|", section, re.M) else 0
            story.append(CondPageBreak(30 * mm + rows * 9 * mm + signature))
        story.extend(parse(section, used))
    return story


def build(markdown: str) -> bytes:
    import io

    text_id = hashlib.sha256(markdown.encode()).hexdigest()[:12]
    out = io.BytesIO()

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(doc.leftMargin, 12 * mm,
                          f"CitCom.ai Data Space · Accession agreement · text {text_id}")
        canvas.drawRightString(A4[0] - doc.rightMargin, 12 * mm, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        out, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=20 * mm,
        bottomMargin=22 * mm, title="Accession agreement to the CitCom.ai Data Space",
        author="CitCom.ai Data Space", subject=f"Text {text_id}", creator=REPO,
        invariant=1)
    doc.build(keep_sections(markdown), onFirstPage=footer, onLaterPages=footer)
    return out.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="fail if the committed PDF does not match the Markdown")
    args = parser.parse_args()
    pdf = build(SOURCE.read_text(encoding="utf-8"))
    if args.check:
        if not TARGET.exists() or TARGET.read_bytes() != pdf:
            print(f"{TARGET.name} is out of date: run python agreements/build_pdf.py",
                  file=sys.stderr)
            return 1
        print(f"{TARGET.name} is up to date")
        return 0
    TARGET.write_bytes(pdf)
    print(f"wrote {TARGET.relative_to(HERE.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
