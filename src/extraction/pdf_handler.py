import PyPDF2
import requests
from typing import Optional
import io
from bs4 import BeautifulSoup

class DocumentHandler:
    @staticmethod
    def extract_text_from_pdf(url: str) -> Optional[str]:
        """Extract text from a PDF URL."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            pdf_file = io.BytesIO(response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = []
            for page in pdf_reader.pages:
                text_content.append(page.extract_text())
            
            return "\n".join(text_content)
            
        except Exception as e:
            print(f"Error extracting PDF text: {str(e)}")
            return None

    @staticmethod
    def extract_text_from_webpage(url: str) -> Optional[str]:
        """Extract text from a webpage."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            print(f"Error extracting webpage text: {str(e)}")
            return None

    @staticmethod
    def get_document_content(url: str) -> Optional[str]:
        """Get content from either PDF or webpage."""
        if url.lower().endswith('.pdf'):
            return DocumentHandler.extract_text_from_pdf(url)
        else:
            return DocumentHandler.extract_text_from_webpage(url)