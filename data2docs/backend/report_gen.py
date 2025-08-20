import pdfkit, tempfile

def save_insights_to_html(insights: str) -> str:
    html_path = tempfile.mktemp(suffix=".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(f"<html><body><h2>AI Insights</h2><p>{insights}</p></body></html>")
    return html_path

def generate_pdf(html_path: str) -> str:
    pdf_path = html_path.replace(".html", ".pdf")
    pdfkit.from_file(html_path, pdf_path)
    return pdf_path
