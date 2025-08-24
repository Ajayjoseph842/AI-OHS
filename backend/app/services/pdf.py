from io import BytesIO
from typing import List, Dict

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

# TODO: Improve layout and add official templates (MOL Form 7, OSHA 300/301)


def generate_audit_binder_pdf(user_email: str, incidents: List[Dict], trainings: List[Dict]) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)

    width, height = LETTER

    # Cover page
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, height - 72, "Hazero - Audit Binder")
    c.setFont("Helvetica", 12)
    c.drawString(72, height - 100, f"Account: {user_email}")

    c.drawString(72, height - 130, "Incidents (summary)")
    y = height - 150
    for inc in incidents[:10]:
        line = f"- {inc.get('incident_date')} | {inc.get('title')} | {inc.get('status')}"
        c.drawString(72, y, line[:110])
        y -= 16
        if y < 100:
            c.showPage()
            y = height - 72

    if y < 200:
        c.showPage()
        y = height - 72

    c.drawString(72, height - 100, "Training Records (summary)")
    y = height - 120
    for tr in trainings[:10]:
        line = f"- {tr.get('assigned_date')} | {tr.get('assignee')} | {tr.get('title')} | {tr.get('status')}"
        c.drawString(72, y, line[:110])
        y -= 16
        if y < 100:
            c.showPage()
            y = height - 72

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()