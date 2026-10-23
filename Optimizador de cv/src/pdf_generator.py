from pathlib import Path
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, ListFlowable, ListItem
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

def build_ats_pdf(cv_data: Dict[str, Any], output_path: str) -> str:
    """
    Genera un documento PDF profesional 100% compatible con lectores ATS usando ReportLab.
    Retorna la ruta absoluta del archivo generado.
    """
    dest_path = Path(output_path).resolve()
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Configuración de márgenes estándar ATS (0.5 pulgadas = 36 pt)
    doc = SimpleDocTemplate(
        str(dest_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    # --- Paleta de Estilos ATS Sobria y Profesional ---
    PRIMARY_COLOR = colors.HexColor("#0F172A")    # Tinta Slate-900
    SECONDARY_COLOR = colors.HexColor("#1E3A8A")  # Azul Autoridad para títulos de sección
    MUTED_COLOR = colors.HexColor("#475569")      # Slate-600 para metadatos
    LINE_COLOR = colors.HexColor("#CBD5E1")       # Slate-300 para divisores sutiles

    # Estilos Tipográficos
    style_name = ParagraphStyle(
        'CVName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=PRIMARY_COLOR,
        alignment=TA_CENTER
    )

    style_title = ParagraphStyle(
        'CVTargetTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=SECONDARY_COLOR,
        alignment=TA_CENTER,
        spaceAfter=4
    )

    style_contact = ParagraphStyle(
        'CVContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=MUTED_COLOR,
        alignment=TA_CENTER
    )

    style_section_heading = ParagraphStyle(
        'CVSectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13,
        textColor=SECONDARY_COLOR,
        spaceBefore=10,
        spaceAfter=2,
        keepWithNext=True
    )

    style_body = ParagraphStyle(
        'CVBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=PRIMARY_COLOR,
        alignment=TA_JUSTIFY
    )

    style_job_role = ParagraphStyle(
        'CVJobRole',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=PRIMARY_COLOR
    )

    style_job_period = ParagraphStyle(
        'CVJobPeriod',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=MUTED_COLOR,
        alignment=TA_RIGHT
    )

    style_job_company = ParagraphStyle(
        'CVJobCompany',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=11,
        textColor=MUTED_COLOR,
        spaceAfter=3
    )

    style_bullet = ParagraphStyle(
        'CVBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12,
        textColor=PRIMARY_COLOR,
        leftIndent=12,
        spaceAfter=2
    )

    style_skill_label = ParagraphStyle(
        'CVSkillLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=PRIMARY_COLOR
    )

    def add_section_divider(title: str):
        """Añade un encabezado de sección con línea divisoria fina."""
        story.append(Paragraph(title.upper(), style_section_heading))
        story.append(HRFlowable(
            width="100%", 
            thickness=0.8, 
            color=LINE_COLOR, 
            spaceBefore=1, 
            spaceAfter=6
        ))

    # =========================================================================
    # 1. ENCABEZADO Y CONTACTO
    # =========================================================================
    name = cv_data.get("full_name", "Profesional")
    target_title = cv_data.get("target_title", "")
    story.append(Paragraph(name, style_name))
    
    if target_title:
        story.append(Paragraph(target_title, style_title))

    # Fila de contacto concatenada limpiamente
    contact_parts = []
    if cv_data.get("email"):
        contact_parts.append(cv_data["email"])
    if cv_data.get("phone"):
        contact_parts.append(cv_data["phone"])
    if cv_data.get("location"):
        contact_parts.append(cv_data["location"])
    if cv_data.get("linkedin"):
        contact_parts.append(cv_data["linkedin"])
    if cv_data.get("portfolio"):
        contact_parts.append(cv_data["portfolio"])

    if contact_parts:
        contact_line = " &nbsp;|&nbsp; ".join(contact_parts)
        story.append(Paragraph(contact_line, style_contact))

    story.append(Spacer(1, 8))

    # =========================================================================
    # 2. RESUMEN PROFESIONAL
    # =========================================================================
    summary = cv_data.get("summary", "").strip()
    if summary:
        add_section_divider("Resumen Profesional")
        story.append(Paragraph(summary, style_body))
        story.append(Spacer(1, 6))

    # =========================================================================
    # 3. EXPERIENCIA LABORAL
    # =========================================================================
    experiences = cv_data.get("experiences", [])
    if experiences:
        add_section_divider("Experiencia Laboral")
        for exp in experiences:
            role = exp.get("role", "")
            company = exp.get("company", "")
            location = exp.get("location", "")
            period = exp.get("period") or f"{exp.get('start_date', '')} - {exp.get('end_date', 'Actual')}"

            # Tabla alineada de 2 columnas: Cargo (izq) y Período/Ubicación (der)
            company_str = f"{company} &nbsp;—&nbsp; {location}" if location else company
            
            exp_table_data = [
                [
                    Paragraph(f"<b>{role}</b>", style_job_role),
                    Paragraph(f"<b>{period}</b>", style_job_period)
                ],
                [
                    Paragraph(company_str, style_job_company),
                    Paragraph("", style_job_period)
                ]
            ]

            t = Table(exp_table_data, colWidths=[360, 180])
            t.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            story.append(t)

            # Viñetas de logros
            achievements = exp.get("achievements", [])
            for ach in achievements:
                story.append(Paragraph(f"• &nbsp;{ach}", style_bullet))

            story.append(Spacer(1, 6))

    # =========================================================================
    # 4. HABILIDADES Y COMPETENCIAS
    # =========================================================================
    skills = cv_data.get("skills", {})
    tech_skills = skills.get("technical", [])
    tools_skills = skills.get("tools", [])
    soft_skills = skills.get("soft", [])

    if tech_skills or tools_skills or soft_skills:
        add_section_divider("Habilidades y Competencias")
        if tech_skills:
            line = f"<b>Tecnologías y Especialidad:</b> {', '.join(tech_skills)}"
            story.append(Paragraph(line, style_body))
            story.append(Spacer(1, 2))
        if tools_skills:
            line = f"<b>Herramientas y Entornos:</b> {', '.join(tools_skills)}"
            story.append(Paragraph(line, style_body))
            story.append(Spacer(1, 2))
        if soft_skills:
            line = f"<b>Competencias Clave:</b> {', '.join(soft_skills)}"
            story.append(Paragraph(line, style_body))
            story.append(Spacer(1, 4))

    # =========================================================================
    # 5. EDUCACIÓN Y CERTIFICACIONES
    # =========================================================================
    education = cv_data.get("education", [])
    certs = cv_data.get("certifications", [])

    if education or certs:
        add_section_divider("Educación y Certificaciones")
        for edu in education:
            degree = edu.get("degree", "")
            institution = edu.get("institution", "")
            year = edu.get("year", "")
            
            edu_table_data = [
                [
                    Paragraph(f"<b>{degree}</b> &nbsp;—&nbsp; {institution}", style_body),
                    Paragraph(year, style_job_period)
                ]
            ]
            t = Table(edu_table_data, colWidths=[420, 120])
            t.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            story.append(t)

        for cert in certs:
            story.append(Paragraph(f"• &nbsp;{cert}", style_bullet))

        story.append(Spacer(1, 4))

    # =========================================================================
    # 6. IDIOMAS
    # =========================================================================
    languages = cv_data.get("languages", [])
    if languages:
        add_section_divider("Idiomas")
        story.append(Paragraph(" &nbsp;|&nbsp; ".join(languages), style_body))

    # Construir PDF
    doc.build(story)
    return str(dest_path)
