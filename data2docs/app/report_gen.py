# app/report_gen.py

import pdfkit
import os

def save_insights_to_html(insights, html_path="templates/report.html"):
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(f"""
        <html>
        <head><title>Data2Docs Report</title></head>
        <body>
            <h1>📊 Data2Docs – AI Insights Report</h1>
            <pre>{insights}</pre>
        </body>
        </html>
        """)
    return html_path

def generate_pdf(html_file="templates/report.html", output_path="reports/output.pdf"):
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        config = pdfkit.configuration(
            wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        )
        pdfkit.from_file(html_file, output_path, configuration=config)
        return output_path
    except Exception as e:
        print("❌ PDF Generation Failed:", e)
        return None
