from __future__ import annotations

from datetime import date
from io import BytesIO

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from utils.processing import format_currency


def generate_rekap_pdf(
    rekap_df: pd.DataFrame,
    start_date: date,
    end_date: date,
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=12,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleCustom",
        parent=styles["Normal"],
        fontSize=11,
        spaceAfter=16,
    )

    story = [
        Paragraph("Rekap Claim Bensin & Parkir", title_style),
        Paragraph(
            f"Periode: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
            subtitle_style,
        ),
    ]

    table_data = [["Shipper", "Bensin", "Parkir", "Total", "Jumlah Outlet"]]
    for _, row in rekap_df.iterrows():
        table_data.append(
            [
                str(row["Shipper"]),
                format_currency(row["Bensin"]),
                format_currency(row["Parkir"]),
                format_currency(row["Total"]),
                str(int(row["Jumlah Outlet"])),
            ]
        )

    table = Table(table_data, repeatRows=1, colWidths=[5 * cm, 4 * cm, 4 * cm, 4 * cm, 4 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#eef4fb")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8fbff")]),
            ]
        )
    )

    story.extend([table, Spacer(1, 0.5 * cm)])
    doc.build(story)
    buffer.seek(0)
    return buffer.read()
