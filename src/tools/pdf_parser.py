import pdfplumber
from typing import Dict, Any, List
import os

class DocumentParser:
    """
    Extracts text and structure from PDF contract documents.
    """
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parses a PDF file and extracts text, metadata, and structure.
        
        Args:
            file_path: Absolute path to the PDF file.
            
        Returns:
            A dictionary containing extracted text, metadata, and structure.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        try:
            with pdfplumber.open(file_path) as pdf:
                full_text = ""
                pages_data = []
                
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    full_text += text + "\n"
                    pages_data.append({
                        "page_number": i + 1,
                        "text": text
                    })
                
                metadata = pdf.metadata
                
                # Basic structure extraction (heuristic based on common headers)
                # This is a simplified version; a real parser would be more robust
                sections = self._extract_sections(full_text)

                return {
                    "text": full_text,
                    "metadata": {
                        "filename": os.path.basename(file_path),
                        "pages": len(pdf.pages),
                        "pdf_metadata": metadata
                    },
                    "structure": {
                        "sections": sections
                    },
                    "pages": pages_data
                }
        except Exception as e:
            raise RuntimeError(f"Failed to parse PDF: {str(e)}")

    def _extract_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Heuristic-based section extraction.
        Looks for lines starting with "1.", "2.", "SECTION", "ARTICLE", etc.
        """
        sections = []
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            stripped = line.strip()
            # Simple heuristic for section headers
            if (stripped.isupper() and len(stripped) < 100) or \
               (stripped.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.", "SECTION", "ARTICLE"))):
                
                if current_section:
                    sections.append(current_section)
                
                current_section = {
                    "title": stripped,
                    "text": ""
                }
            elif current_section:
                current_section["text"] += line + "\n"
        
        if current_section:
            sections.append(current_section)
            
        return sections

if __name__ == "__main__":
    # Simple test
    # parser = DocumentParser()
    # print(parser.parse("path/to/test.pdf"))
    pass
