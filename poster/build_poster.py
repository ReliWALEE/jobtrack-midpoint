"""Build the 42 x 56 inch JobTrack poster from verified project evidence.

Run with the bundled Python runtime that includes reportlab. A file labeled
DRAFT is produced until deployment, role, extension, and metric data are set.
"""

import argparse
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
PAGE_W, PAGE_H = 42 * 72, 56 * 72
NAVY = colors.HexColor("#13283f")
BLUE = colors.HexColor("#216d92")
TEAL = colors.HexColor("#247aa0")
MUTED = colors.HexColor("#486075")
PAPER = colors.HexColor("#f7fafc")
PALE = colors.HexColor("#eaf3f8")
LINE = colors.HexColor("#c5d7e2")
WHITE = colors.white
MARGIN = 110
GAP = 48
COL = (PAGE_W - 2 * MARGIN - 2 * GAP) / 3


def fonts():
    pdfmetrics.registerFont(TTFont("Arial", "/System/Library/Fonts/Supplemental/Arial.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-Bold", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"))
    pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold")


def para(canvas, text, x, top, width, size=30, leading=None, color=MUTED, bold=False):
    style = ParagraphStyle(
        "body", fontName="Arial-Bold" if bold else "Arial", fontSize=size,
        leading=leading or size * 1.31, textColor=color, spaceAfter=0,
    )
    paragraph = Paragraph(text, style)
    _, height = paragraph.wrap(width, 2000)
    paragraph.drawOn(canvas, x, top - height)
    return top - height


def panel(canvas, x, top, width, title, paragraphs, *, min_height=0, fill=WHITE):
    content_w = width - 62
    heights = []
    for value in paragraphs:
        style = ParagraphStyle("measure", fontName="Arial", fontSize=32, leading=42)
        item = Paragraph(value, style)
        heights.append(item.wrap(content_w, 1800)[1])
    height = max(min_height, 118 + sum(heights) + 24 * max(len(heights) - 1, 0) + 44)
    bottom = top - height
    canvas.setFillColor(fill)
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(2)
    canvas.roundRect(x, bottom, width, height, 24, fill=1, stroke=1)
    canvas.setFillColor(NAVY)
    canvas.setFont("Arial-Bold", 42)
    canvas.drawString(x + 31, top - 65, title)
    y = top - 115
    for value in paragraphs:
        y = para(canvas, value, x + 31, y, content_w, size=32, leading=42)
        y -= 24
    return bottom


def draw_image(canvas, path, x, y, width, height):
    from reportlab.lib.utils import ImageReader
    canvas.drawImage(ImageReader(str(path)), x, y, width=width, height=height, mask="auto")


def architecture_panel(canvas, top):
    x = MARGIN
    width = COL * 2 + GAP
    height = 1130
    bottom = top - height
    canvas.setFillColor(WHITE)
    canvas.setStrokeColor(LINE)
    canvas.roundRect(x, bottom, width, height, 24, fill=1, stroke=1)
    diagram = ROOT / "docs" / "architecture-poster.png"
    if not diagram.exists():
        raise FileNotFoundError(f"Render docs/architecture.svg to {diagram} first")
    img_w = width - 44
    img_h = img_w * 820 / 1500
    draw_image(canvas, diagram, x + 22, bottom + (height - img_h) / 2, img_w, img_h)
    return bottom


def summary_panel(canvas, top, evidence):
    x = MARGIN + 2 * (COL + GAP)
    paragraphs = [
        "JobTrack keeps a student's job applications in one searchable pipeline. It stores company, role, location, annual salary, status, date, link, and notes.",
        "The dashboard, Python API, and SQLite support tracking and job discovery. Remotive works without a key; Indeed and LinkedIn use optional JSearch. A Chrome extension reads structured postings.",
    ]
    if evidence.get("aws_verified"):
        paragraphs.append("Verified private AWS sandbox deployment: EC2, encrypted EBS, private S3 source delivery, IAM, CloudFormation, and a restricted SSH tunnel.")
    else:
        paragraphs.append("AWS deployment is still pending verification in this draft. Final output must state actual cloud results.")
    return panel(canvas, x, top, COL, "Project summary", paragraphs, min_height=1130, fill=PALE)


def screenshot_panel(canvas, x, top):
    width = COL
    height = 800
    bottom = top - height
    canvas.setFillColor(WHITE)
    canvas.setStrokeColor(LINE)
    canvas.roundRect(x, bottom, width, height, 24, fill=1, stroke=1)
    canvas.setFillColor(NAVY)
    canvas.setFont("Arial-Bold", 39)
    canvas.drawString(x + 31, top - 61, "Application dashboard")
    path = ROOT / "docs" / "dashboard-final-local.png"
    if not path.exists():
        path = ROOT / "docs" / "dashboard.png"
    img_w = width - 60
    img_h = img_w * 1110 / 1440
    draw_image(canvas, path, x + 30, top - 111 - img_h, img_w, img_h)
    para(canvas, "Fictional demonstration records; screenshot captured locally.", x + 31,
         bottom + 104, width - 62, size=23, leading=28)
    return bottom


def metrics_panel(canvas, x, top, evidence, metrics):
    width = COL
    height = 864
    bottom = top - height
    canvas.setFillColor(PALE)
    canvas.setStrokeColor(LINE)
    canvas.roundRect(x, bottom, width, height, 24, fill=1, stroke=1)
    canvas.setFillColor(NAVY)
    canvas.setFont("Arial-Bold", 39)
    is_aws = bool(evidence.get("aws_verified"))
    canvas.drawString(x + 31, top - 61, "Performance evaluation" if is_aws else "Local baseline only")
    if not metrics:
        para(canvas, "Performance measurements are pending. The final poster will use observed latency from the deployed instance and state the sample size, record count, region, and instance type.",
             x + 31, top - 120, width - 62, size=30, leading=40)
        return bottom
    results = metrics["results"]
    labels = [("Health", "health"), ("List all", "list_all"), ("Search", "search_engineer")]
    max_p95 = max(results[key]["p95_ms"] for _, key in labels) or 1
    y = top - 143
    chart_x = x + 267
    chart_w = width - 330
    for label, key in labels:
        item = results[key]
        canvas.setFillColor(NAVY)
        canvas.setFont("Arial-Bold", 27)
        canvas.drawString(x + 31, y - 25, label)
        median_width = chart_w * item["median_ms"] / max_p95
        p95_width = chart_w * item["p95_ms"] / max_p95
        canvas.setFillColor(colors.HexColor("#98c9dc"))
        canvas.roundRect(chart_x, y - 32, p95_width, 42, 10, fill=1, stroke=0)
        canvas.setFillColor(TEAL)
        canvas.roundRect(chart_x, y - 32, median_width, 42, 10, fill=1, stroke=0)
        canvas.setFillColor(MUTED)
        canvas.setFont("Arial", 23)
        canvas.drawRightString(x + width - 30, y - 61,
                               f"median {item['median_ms']:.2f} ms · p95 {item['p95_ms']:.2f} ms")
        y -= 150
    if is_aws:
        region = evidence.get("region", "region not recorded")
        machine = evidence.get("instance_type", "instance type not recorded")
        location = f"{machine}, {region}; includes the client-to-EC2 SSH tunnel."
    else:
        location = "localhost only; excludes AWS and the SSH tunnel. Cloud measurement pending."
    caption = (f"{metrics['requests_per_endpoint']} sequential GET requests per endpoint after "
               f"{metrics['warmup_per_endpoint']} warmups; {metrics['database_records']} fictional records. "
               f"{location} Small single-user sample.")
    para(canvas, caption, x + 31, y - 7, width - 62, size=25, leading=32)
    return bottom


def build(output, evidence, metrics):
    fonts()
    output.parent.mkdir(parents=True, exist_ok=True)
    c = Canvas(str(output), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    c.setTitle("JobTrack - Group 42 final project poster")
    c.setAuthor("Ahmad Salem; NoorAldeen Waleed")
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 355, PAGE_W, 355, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont("Arial-Bold", 101)
    c.drawString(MARGIN, PAGE_H - 161, "JobTrack")
    c.setFont("Arial", 43)
    c.drawString(MARGIN, PAGE_H - 230,
                 "A private cloud-hosted job application tracker" if evidence.get("aws_verified")
                 else "A private job application tracker · AWS deployment planned")
    c.setFont("Arial", 29)
    c.drawString(MARGIN, PAGE_H - 298, "CSE 4333 Cloud Computing · Group 42")
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 298, "Ahmad Salem · NoorAldeen Waleed")

    top = PAGE_H - 412
    architecture_panel(c, top)
    summary_panel(c, top, evidence)
    lower_top = top - 1178
    x1, x2, x3 = MARGIN, MARGIN + COL + GAP, MARGIN + 2 * (COL + GAP)

    y1 = screenshot_panel(c, x1, lower_top) - 28
    y1 = panel(c, x1, y1, COL, "Introduction · users", [
        "Students and recent graduates often manage many applications at once and lose track of dates and next steps.",
        "JobTrack keeps opportunities, status changes, salary, and notes together so a user can see their pipeline and act on it.",
    ]) - 28
    y1 = panel(c, x1, y1, COL, "User workflow", [
        "Find a listing or import a posting draft; review fields; save; update status; search and filter; delete old entries.",
        "Remotive and optional JSearch provide job discovery. The extension reads Schema.org JobPosting JSON-LD. JobTrack does not apply to employers.",
    ]) - 28
    y1 = panel(c, x1, y1, COL, "Conclusion", [
        "JobTrack puts discovered opportunities and application progress in one searchable place. It is a working private single-user demonstration.",
        "AWS deployment and performance are described using measured results; public multi-user hosting remains future work." if evidence.get("aws_verified") else "Cloud deployment and measurement remain unverified; the local demonstration is functional.",
    ])

    y2 = panel(c, x2, lower_top, COL, "Application logic", [
        "The responsive dashboard calls same-origin JSON endpoints. The Python API validates fields and stores UTC timestamps in SQLite.",
        "Endpoints cover health, application CRUD, /api/jobs discovery, /api/job-sources status, and saving a listing. Search and filters combine; sort keys are allowlisted.",
    ]) - 28
    cloud_intro = ("CloudFormation provisions EC2, encrypted EBS, and a security group allowing SSH only from one trusted /32. The sandbox's myS3Role profile pulls source from private S3."
                   if evidence.get("aws_verified") else
                   "Planned cloud design: CloudFormation would provision EC2, encrypted EBS, and SSH restricted to one /32, using the sandbox's myS3Role profile for private S3.")
    y2 = panel(c, x2, y2, COL, "Cloud services", [
        cloud_intro,
        "An SSH tunnel would let an authorized user reach the loopback-only app without opening a public web port." if not evidence.get("aws_verified") else "An SSH tunnel lets an authorized user reach the loopback-only app without opening a public web port.",
    ]) - 28
    y2 = panel(c, x2, y2, COL, "Alternatives considered", [
        "A public HTTPS app needs login and per-user authorization. RDS or DynamoDB would improve managed storage; serverless hosting could scale differently.",
        "The one-instance SQLite design is appropriate for a small private class demo, but it has no high availability or automatic backup.",
    ]) - 28
    y2 = panel(c, x2, y2, COL, "Challenges and lessons", [
        "Browser QA exposed a Reset-button conflict. Final API review exposed unclosed SQLite connections. Both were fixed and regression-tested.",
        "A restricted SSH tunnel keeps the web service private. The sandbox session is time-limited; the EBS root volume needs a backup before termination.",
    ]) - 28
    roles = evidence.get("roles") or "Team roles await confirmation. The proposal credits NoorAldeen with the idea and Ahmad with proposal review; final work should be described accurately."
    y2 = panel(c, x2, y2, COL, "Team contributions", [roles])

    y3 = metrics_panel(c, x3, lower_top, evidence, metrics) - 28
    y3 = panel(c, x3, y3, COL, "Verification", [
        "23 Python tests and 5 extractor tests pass. The browser checked draft review, save, edit, refresh, filters, sorting, deletion, and job discovery.",
        "Cloud CRUD, restart persistence, and Remotive discovery passed through the SSH tunnel. The installed extension toolbar was not tested.",
    ]) - 28
    y3 = panel(c, x3, y3, COL, "Machine learning", [
        "Not applicable. JobTrack uses rules and a relational database; it has no trained model.",
    ]) - 28
    y3 = panel(c, x3, y3, COL, "Future work", [
        "Add authentication and user isolation before public access. Move to managed backup/database, add HTTPS and monitoring, and broaden posting extraction.",
    ])

    footer_y = 88
    c.setStrokeColor(LINE)
    c.setLineWidth(2)
    c.line(MARGIN, footer_y + 82, PAGE_W - MARGIN, footer_y + 82)
    c.setFillColor(NAVY)
    c.setFont("Arial-Bold", 25)
    c.drawString(MARGIN, footer_y + 40, "Ahmad Salem · afs1009@mavs.uta.edu")
    c.drawRightString(PAGE_W - MARGIN, footer_y + 40,
                      "NoorAldeen Waleed · nxw3312@mavs.uta.edu")
    if min(y1, y2, y3) < footer_y + 110:
        raise RuntimeError(f"Poster content reaches footer: {y1:.0f}, {y2:.0f}, {y3:.0f}")
    c.showPage()
    c.save()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, default=ROOT / "poster" / "evidence.json")
    parser.add_argument("--metrics", type=Path, default=ROOT / "evidence" / "performance-aws.json")
    parser.add_argument("--output", type=Path, default=ROOT / "work" / "JobTrack-poster-DRAFT.pdf")
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_text()) if args.evidence.exists() else {}
    metrics = json.loads(args.metrics.read_text()) if args.metrics.exists() else None
    if args.output.name.upper().find("DRAFT") < 0 and (not evidence.get("aws_verified") or not metrics or not evidence.get("roles")):
        raise SystemExit("Refusing to create final poster without verified AWS evidence, metrics, and team roles")
    if metrics is None and not evidence.get("aws_verified"):
        local_path = ROOT / "evidence" / "performance-local.json"
        metrics = json.loads(local_path.read_text()) if local_path.exists() else None
    build(args.output, evidence, metrics)
    print(args.output)


if __name__ == "__main__":
    main()
