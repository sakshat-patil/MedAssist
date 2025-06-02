from typing import Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import os
from datetime import datetime

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        # Create reports directory if it doesn't exist
        os.makedirs("reports", exist_ok=True)

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        ))
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12
        ))
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12
        ))

    def generate_report(self, data: Dict[str, Any]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        # Title
        story.append(Paragraph("Medical Triage Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))

        # Risk Assessment
        story.append(Paragraph("Risk Assessment", self.styles['CustomHeading']))
        story.append(Paragraph(f"Risk Level: {data['risk_assessment']['risk_level']}", self.styles['CustomBody']))
        story.append(Paragraph(f"Explanation: {data['risk_assessment']['explanation']}", self.styles['CustomBody']))
        story.append(Spacer(1, 12))

        # Symptoms
        story.append(Paragraph("Symptoms", self.styles['CustomHeading']))
        symptoms_data = [["Description", "Severity"]]
        for symptom in data['structured_data']['symptoms']:
            symptoms_data.append([symptom['description'], symptom['severity']])
        
        symptoms_table = Table(symptoms_data, colWidths=[4*inch, 2*inch])
        symptoms_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(symptoms_table)
        story.append(Spacer(1, 12))

        # Vital Signs
        story.append(Paragraph("Vital Signs", self.styles['CustomHeading']))
        vitals = data['structured_data']['vital_signs']
        vitals_data = [
            ["Blood Pressure", f"{vitals['blood_pressure']['systolic']}/{vitals['blood_pressure']['diastolic']} mmHg"],
            ["Heart Rate", f"{vitals['heart_rate']} bpm"],
            ["Temperature", f"{vitals['temperature']['value']}°{vitals['temperature']['unit']}"],
            ["Oxygen Saturation", f"{vitals['oxygen_saturation']}%"]
        ]
        
        vitals_table = Table(vitals_data, colWidths=[2*inch, 4*inch])
        vitals_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(vitals_table)
        story.append(Spacer(1, 12))

        # Medical History
        story.append(Paragraph("Medical History", self.styles['CustomHeading']))
        for condition in data['structured_data']['medical_history']:
            story.append(Paragraph(f"• {condition}", self.styles['CustomBody']))
        story.append(Spacer(1, 12))

        # Build PDF
        doc.build(story)
        return buffer.getvalue()

    def save_report(self, data: Dict[str, Any]) -> str:
        """Generate and save the PDF report to a file."""
        try:
            # Generate PDF content
            pdf_content = self.generate_report(data)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"medical_triage_report_{timestamp}.pdf"
            filepath = os.path.join("reports", filename)
            
            # Save to file
            with open(filepath, "wb") as f:
                f.write(pdf_content)
            
            return filepath
        except Exception as e:
            raise Exception(f"Error saving PDF report: {str(e)}")
