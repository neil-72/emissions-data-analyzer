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
            # Use stream=True for large files
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Download the PDF in chunks
            pdf_content = bytearray()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    pdf_content.extend(chunk)
            
            # Read PDF content
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract text from all pages
            text_content = []
            for page in pdf_reader.pages:
                try:
                    text_content.append(page.extract_text())
                except Exception as e:
                    print(f"Warning: Could not extract text from page: {str(e)}")
                    continue
            
            return "\n".join(text_content)
            
        except Exception as e:
            print(f"Error extracting PDF text: {str(e)}")
            return None

    @staticmethod
    def extract_text_from_webpage(url: str) -> Optional[str]:
        """Extract text from a webpage."""
        try:
            response = requests.get(url, timeout=30)
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