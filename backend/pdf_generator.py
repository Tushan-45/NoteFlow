from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus.tables import Table, TableStyle

from reportlab.lib.pagesizes import letter

import re


def create_pdf(content, filename="notes.pdf"):

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    elements = []

    lines = content.split("\n")

    for line in lines:

        line = line.strip()

        if not line:
            elements.append(Spacer(1, 12))
            continue

        # Headings
        if "**" in line:

            heading = line.replace("**", "")

            p = Paragraph(
                f'<font color="blue"><b>{heading}</b></font>',
                styles['Heading2']
            )

            elements.append(p)

        # Timestamps
        elif re.search(r'\[\d{2}:\d{2}\]', line):

            p = Paragraph(
                f'<font color="green"><b>{line}</b></font>',
                styles['BodyText']
            )

            elements.append(p)

        # Normal text
        else:

            p = Paragraph(
                line,
                styles['BodyText']
            )

            elements.append(p)

        elements.append(Spacer(1, 8))

    doc.build(elements)

    return filename