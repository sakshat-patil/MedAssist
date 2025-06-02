from typing import Dict, Any
import PyPDF2
from docx import Document
import io

class DocumentProcessor:
    def __init__(self):
        self.supported_formats = {
            'application/pdf': self._process_pdf,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': self._process_docx,
            'text/plain': self._process_txt
        }

    async def process_file(self, file) -> str:
        """Process uploaded file and extract text content."""
        try:
            content = await file.read()
            content_type = file.content_type
            
            if content_type not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {content_type}")
            
            # Process the file based on its type
            text_content = self.supported_formats[content_type](content)
            
            return text_content
        except Exception as e:
            raise Exception(f"Error processing file: {str(e)}")

    def _process_pdf(self, content: bytes) -> str:
        """Extract text from PDF file."""
        try:
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")

    def _process_docx(self, content: bytes) -> str:
        """Extract text from DOCX file."""
        try:
            docx_file = io.BytesIO(content)
            doc = Document(docx_file)
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text
        except Exception as e:
            raise Exception(f"Error processing DOCX: {str(e)}")

    def _process_txt(self, content: bytes) -> str:
        """Extract text from TXT file."""
        try:
            return content.decode('utf-8')
        except Exception as e:
            raise Exception(f"Error processing TXT: {str(e)}") 