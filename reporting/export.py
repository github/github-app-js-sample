# reporting/export.py
import pandas as pd
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import datetime
import os

# TODO: IMPORTANT - Jalali Font Handling for PDF
# 1. Ensure you have a Jalali font file (e.g., Vazir.ttf, Sahel.ttf) in your project.
# 2. Update FONT_PATH to the correct path of your .ttf file.
# 3. Register the font with ReportLab.
# 4. Use the registered font name in ParagraphStyles and TableStyles.

FONT_NAME = "Vazir" # Default to Vazir, can be changed
FONT_PATH = "Vazir.ttf" # Assume Vazir.ttf is in the same directory or a known path

# Attempt to register the Jalali font
# This should ideally be done once when the application starts,
# but for this module, we can try it here.
try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
        JALALI_FONT_AVAILABLE = True
        print(f"Successfully registered font: {FONT_NAME} from {FONT_PATH}")
    else:
        JALALI_FONT_AVAILABLE = False
        print(f"WARNING: Jalali font '{FONT_NAME}' not found at '{FONT_PATH}'. PDF output may not render Persian text correctly.")
        FONT_NAME = 'Helvetica' # Fallback font
except Exception as e:
    JALALI_FONT_AVAILABLE = False
    print(f"ERROR: Could not register font '{FONT_NAME}' from '{FONT_PATH}'. PDF output will use fallback. Error: {e}")
    FONT_NAME = 'Helvetica' # Fallback font


def export_to_excel(dataframe: pd.DataFrame, file_path: str, report_title: str):
    """Exports a Pandas DataFrame to an Excel file."""
    try:
        # Use a sheet name that's less likely to cause issues, or use report_title if simple
        sheet_name = report_title[:30] # Excel sheet names have a length limit
        dataframe.to_excel(file_path, index=False, sheet_name=sheet_name)
        print(f"Report '{report_title}' successfully exported to Excel: {file_path}")
    except Exception as e:
        print(f"Error exporting to Excel: {e}")
        raise # Re-raise to be caught by UI

def export_to_pdf(dataframe: pd.DataFrame, file_path: str, report_info: dict):
    """
    Exports a Pandas DataFrame to a PDF file using ReportLab.
    report_info is a dict containing 'title', 'start_date', 'end_date', etc.
    """
    try:
        doc = SimpleDocTemplate(file_path, pagesize=landscape(letter))
        story = []
        styles = getSampleStyleSheet()

        # Custom style for Persian text
        # Ensure FONT_NAME is correctly set (e.g., to 'Vazir')
        persian_style_normal = ParagraphStyle(
            'PersianNormal',
            parent=styles['Normal'],
            fontName=FONT_NAME, # Use the registered Jalali font
            fontSize=10,
            leading=14,
            alignment=1 # 0=left, 1=center, 2=right, 4=justify (for Farsi, right is common for body)
        )
        persian_style_heading = ParagraphStyle(
            'PersianHeading',
            parent=styles['h1'],
            fontName=FONT_NAME,
            fontSize=14,
            leading=18,
            alignment=1 # Center align headings
        )
        persian_style_table_header = ParagraphStyle(
            'PersianTableHeader',
            parent=persian_style_normal,
            fontName=FONT_NAME, # Ensure bold version of font is registered if needed, or use base
            alignment=1, # Center
            textColor=colors.whitesmoke
        )
        persian_style_table_cell = ParagraphStyle(
            'PersianTableCell',
            parent=persian_style_normal,
            fontName=FONT_NAME,
            alignment=1 # Center for table cells, adjust as needed
        )


        # Report Title
        title_text = report_info.get('title', "گزارش")
        story.append(Paragraph(title_text, persian_style_heading))
        story.append(Spacer(1, 0.2 * inch))

        # Report Filters/Date Range
        date_range_text = f"تاریخ گزارش: از {report_info['start_date']} تا {report_info['end_date']}"
        story.append(Paragraph(date_range_text, persian_style_normal))
        story.append(Spacer(1, 0.2 * inch))

        # Current Date
        # TODO: Convert to Jalali if Jalali font is available and jdatetime is integrated
        current_time_text = f"تاریخ صدور گزارش: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        story.append(Paragraph(current_time_text, persian_style_normal))
        story.append(Spacer(1, 0.3 * inch))


        if dataframe.empty:
            story.append(Paragraph("داده ای برای نمایش در این گزارش یافت نشد.", persian_style_normal))
        else:
            # Convert DataFrame to list of lists for ReportLab Table
            # Apply Paragraph style to each cell for Farsi text handling

            # Headers
            table_header_data = [Paragraph(str(col), persian_style_table_header) for col in dataframe.columns]

            # Data cells
            table_body_data = []
            for index, row in dataframe.iterrows():
                table_body_data.append([Paragraph(str(x), persian_style_table_cell) for x in row])

            table_data = [table_header_data] + table_body_data

            pdf_table = Table(table_data, repeatRows=1) # Repeat headers on each page

            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F81BD")), # Header background
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), FONT_NAME), # Header font (use bold if available)
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#DCE6F1")), # Body background (alternating if needed)
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), FONT_NAME), # Body font
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0,0), (-1,-1), 3),
                ('RIGHTPADDING', (0,0), (-1,-1), 3),
            ])
            pdf_table.setStyle(table_style)
            story.append(pdf_table)

        doc.build(story)
        print(f"Report '{report_info['title']}' successfully exported to PDF: {file_path}")

    except Exception as e:
        print(f"Error exporting to PDF: {e}")
        raise

if __name__ == '__main__':
    # Example Usage for PDF export (for testing)
    # Ensure Vazir.ttf (or your chosen font) is in the same directory as this script, or provide the full path.

    print(f"Testing PDF Export. Jalali Font Available: {JALALI_FONT_AVAILABLE}, Using Font: {FONT_NAME}")

    # Sample data
    sample_data = {
        'نام راننده': ['احمد محمدی', 'زهرا حسینی', 'علی کریمی'],
        'تعداد ماموریت': [10, 15, 12],
        'ساعات کارکرد': [40.5, 60.2, 55.0],
        'نوع خودرو اصلی': ['سمند', 'پژو ۴۰۵', 'پراید ۱۳۱']
    }
    sample_df = pd.DataFrame(sample_data)

    report_details = {
        'title': "نمونه گزارش عملکرد رانندگان",
        'start_date': datetime.date(2023, 1, 1).strftime('%Y-%m-%d'),
        'end_date': datetime.date(2023, 1, 31).strftime('%Y-%m-%d'),
    }

    pdf_file_path = "sample_report.pdf"
    excel_file_path = "sample_report.xlsx"

    try:
        export_to_pdf(sample_df, pdf_file_path, report_details)
        print(f"Sample PDF report generated: {pdf_file_path}")
    except Exception as e_pdf:
        print(f"Error generating sample PDF: {e_pdf}")

    try:
        export_to_excel(sample_df, excel_file_path, "Sample Report")
        print(f"Sample Excel report generated: {excel_file_path}")
    except Exception as e_excel:
        print(f"Error generating sample Excel: {e_excel}")

    # Test with empty dataframe
    empty_df = pd.DataFrame()
    try:
        export_to_pdf(empty_df, "empty_report.pdf", {'title': "گزارش خالی", 'start_date': 'N/A', 'end_date': 'N/A'})
        print("Empty PDF report generated successfully.")
    except Exception as e_empty_pdf:
        print(f"Error generating empty PDF: {e_empty_pdf}")
