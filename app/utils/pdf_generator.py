from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import BACKEND_DIR, PAYSLIPS_DIR
from app.models.employee import Employee
from app.models.payslip import Payslip

COMPANY_ADDRESS = (
    "Faiyaz Center, Office No: 08, Shahrah-e-Faisal Rd, "
    "SMCHS Block A, Karachi, Pakistan"
)
LOGO_PATH = BACKEND_DIR / "app" / "assets" / "companylogo.png"

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

PRIMARY = colors.HexColor("#1E3D5A")
TEXT = colors.HexColor("#1A202C")
MUTED = colors.HexColor("#64748B")
BORDER = colors.HexColor("#CBD5E1")
HEADER_BG = colors.HexColor("#F1F5F9")


def _format_amount(value: float) -> str:
    if not value:
        return "-"
    return f"{int(value):,}"


def _format_payslip_month(month: int, year: int) -> str:
    return f"{MONTH_NAMES[month - 1]}-{year}"


def _format_payslip_number(payslip_id: int) -> str:
    return str(payslip_id).zfill(5)


def _build_earnings_table(styles):
    return TableStyle(
        [
            ("SPAN", (0, 0), (1, 0)),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#334155")),
            ("TEXTCOLOR", (0, 1), (-1, -1), TEXT),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
    )


def generate_payslip_pdf(payslip: Payslip, employee: Employee) -> str:
    PAYSLIPS_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"payslip_{employee.employee_code}_{payslip.month:02d}_{payslip.year}.pdf"
    file_path = PAYSLIPS_DIR / filename
    relative_path = f"payslips/{filename}"

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=45,
        bottomMargin=45,
    )

    content_width = A4[0] - doc.leftMargin - doc.rightMargin
    half_width = content_width / 2

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PayslipTitle",
        parent=styles["Normal"],
        fontSize=16,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=16,
        textColor=TEXT,
    )
    address_style = ParagraphStyle(
        "Address",
        parent=styles["Normal"],
        fontSize=8,
        textColor=MUTED,
        leading=12,
        alignment=TA_LEFT,
    )
    meta_label_style = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=MUTED,
        alignment=TA_RIGHT,
    )
    month_style = ParagraphStyle(
        "Month",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica-Bold",
        textColor=PRIMARY,
        alignment=TA_RIGHT,
        spaceBefore=4,
    )
    employee_style = ParagraphStyle(
        "Employee",
        parent=styles["Normal"],
        fontSize=9,
        leading=15,
        textColor=TEXT,
        alignment=TA_LEFT,
        leftIndent=0,
    )
    net_style = ParagraphStyle(
        "NetSalary",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica-Bold",
        textColor=TEXT,
        spaceBefore=4,
        spaceAfter=12,
        alignment=TA_LEFT,
        leftIndent=0,
    )
    note_style = ParagraphStyle(
        "Note",
        parent=styles["Normal"],
        fontSize=7.5,
        textColor=MUTED,
        leading=11,
        spaceBefore=8,
    )

    elements = []

    # 1. PAYSLIP title (same order as web UI)
    elements.append(Paragraph("PAYSLIP", title_style))

    # 2. Header: logo + address | payslip meta (full width, left-aligned)
    logo_flow = Spacer(1, 1)
    if LOGO_PATH.exists():
        logo_flow = Image(str(LOGO_PATH), width=1.15 * inch, height=1 * inch)
        logo_flow.hAlign = "LEFT"

    left_col = Table(
        [[logo_flow], [Paragraph(COMPANY_ADDRESS, address_style)]],
        colWidths=[content_width * 0.55],
    )
    left_col.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (0, 0), 6),
            ]
        )
    )

    right_col = [
        Paragraph(
            f'Payslip# <b><font color="#1A202C">{_format_payslip_number(payslip.id)}</font></b>',
            meta_label_style,
        ),
        Paragraph(
            f"Salary Month of {_format_payslip_month(payslip.month, payslip.year)}",
            month_style,
        ),
    ]

    header_table = Table(
        [[left_col, right_col]],
        colWidths=[content_width * 0.55, content_width * 0.45],
    )
    header_table.hAlign = "LEFT"
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ]
        )
    )
    elements.append(header_table)
    elements.append(Spacer(1, 0.12 * inch))

    # 3. Employee info
    elements.append(Paragraph(f"<b>Name :</b> {employee.full_name}", employee_style))
    elements.append(
        Paragraph(
            f"<b>Designation :</b> {employee.designation or '—'}",
            employee_style,
        )
    )
    elements.append(
        Paragraph(
            f"<b>Employee ID :</b> # {employee.employee_code}",
            employee_style,
        )
    )
    elements.append(Spacer(1, 0.12 * inch))

    # 4. Earnings | Deductions (two tables side by side, matching web)
    earnings_data = [
        ["Earnings", ""],
        ["Basic Salary", _format_amount(payslip.basic_salary)],
        ["Bonus", _format_amount(payslip.allowances)],
        ["Over Time", "-"],
    ]
    deductions_data = [
        ["Deductions", ""],
        ["Tax Deduction", _format_amount(payslip.deductions)],
        ["PF", "-"],
        ["Loan", "-"],
    ]

    earnings_table = Table(
        earnings_data,
        colWidths=[half_width * 0.62, half_width * 0.38],
    )
    earnings_table.setStyle(_build_earnings_table(styles))

    deductions_table = Table(
        deductions_data,
        colWidths=[half_width * 0.62, half_width * 0.38],
    )
    deductions_table.setStyle(_build_earnings_table(styles))

    combined_table = Table(
        [[earnings_table, deductions_table]],
        colWidths=[half_width, half_width],
    )
    combined_table.hAlign = "LEFT"
    combined_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                ("LINEAFTER", (0, 0), (0, 0), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    elements.append(combined_table)

    # 5. Net salary (plain text like web — no colored bar)
    elements.append(
        Paragraph(
            f"Net Salary : {_format_amount(payslip.net_salary)}/-",
            net_style,
        )
    )

    # 6. Footer note
    elements.append(
        Paragraph(
            "Note: This is a system generated receipt and will only be valid with proper "
            "signed and stamped by <b>COMPUTING YARD</b>.",
            note_style,
        )
    )

    doc.build(elements)
    return relative_path
