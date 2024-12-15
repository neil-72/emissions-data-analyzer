import PyPDF2
import requests
from typing import Optional, List, Dict
import io
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin

class DocumentHandler:
    @staticmethod
    def extract_text_from_pdf(url: str, retries: int = 3) -> Optional[str]:
        """Extract text from a PDF URL with retries and fallbacks."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for attempt in range(retries):
            try:
                # Try direct download first
                response = requests.get(url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()
                
                # Download PDF in chunks
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
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    # Try alternative URLs or web archive
                    alt_urls = DocumentHandler._get_alternative_urls(url)
                    for alt_url in alt_urls:
                        try:
                            return DocumentHandler.extract_text_from_pdf(alt_url, retries=1)
                        except:
                            continue
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
        
        return None

    @staticmethod
    def _get_alternative_urls(url: str) -> List[str]:
        """Generate alternative URLs to try."""
        alternatives = []
        
        # Try web archive
        alternatives.append(f"https://web.archive.org/web/2024/{url}")
        
        # Try different domains
        if "images." in url:
            alternatives.append(url.replace("images.", "www."))
        
        # Try different file paths
        base_url = url.rsplit('/', 1)[0]
        filename = url.rsplit('/', 1)[1]
        alternatives.append(urljoin(base_url + '/documents/', filename))
        alternatives.append(urljoin(base_url + '/downloads/', filename))
        
        return alternatives

    @staticmethod
    def extract_text_from_webpage(url: str) -> Optional[str]:
        """Extract text from a webpage."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            
            # Look for main content areas
            main_content = soup.find(["main", "article", "div", "body"])
            if main_content:
                text = main_content.get_text()
            else:
                text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            return ' '.join(chunk for chunk in chunks if chunk)
            
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