from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import re
from reportlab.lib.utils import simpleSplit

def clean_text(text: str):
    """Remove Markdown symbols for PDF output."""
    text = re.sub(r"[*#`]+", "", text)  # strip *, #, `
    return text.strip()

def format_reg_info(reg_info):
    if not reg_info or "error" in reg_info[0]:
        return "No specific regulatory data found"
    funcs = []
    names = []
    for entry in reg_info:
        if entry.get("functions"):
            funcs.extend(entry["functions"])
        if entry.get("incinamefull"):
            names.append(entry["incinamefull"])
    funcs = list(set(funcs))
    names = list(set(names))
    return f"Functions: {', '.join(funcs)} | Related INCI: {', '.join(names[:3])}"

def generate_pdf_report(name: str, ingredients: dict, report: dict, output_path: str):
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    y = height - 50

    def write_wrapped(text, x=70, max_width=460, line_height=14):
        nonlocal y
        lines = simpleSplit(text, 'Helvetica', 12, max_width)
        for line in lines:
            c.drawString(x, y, line)
            y -= line_height
            if y < 100:  # new page
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 12)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"Compliance Report: {name}")
    y -= 40
    c.setFont("Helvetica", 12)

    # Ingredients
    for item in report["raw_results"]:
        write_wrapped(f"{item['ingredient']} ({item['concentration']}) → {item['status']}")
        reg_info = item.get("regulatory_info", [])


        if reg_info:
            write_wrapped(f"Regulatory Info: {format_reg_info(item['regulatory_info'])}", x=90)

    # Summary
    y -= 20
    write_wrapped("Summary:")
    summary = report.get("markdown_report", "")
    cleaned_summary = clean_text(summary)
    write_wrapped(cleaned_summary, x=90)

    c.save()
