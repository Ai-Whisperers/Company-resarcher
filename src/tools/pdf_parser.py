import os
from typing import Optional
from ..core.logger import setup_logger

logger = setup_logger("pdf_parser")


class PDFParser:
    """
    Parses PDF documents using LlamaParse for high-quality extraction,
    with a fallback to PyPDF for basic text extraction.
    """

    def __init__(self):
        self.llama_api_key = os.getenv("LLAMA_CLOUD_API_KEY")
        self.use_llama = bool(self.llama_api_key)

        if not self.use_llama:
            logger.warning(
                "LLAMA_CLOUD_API_KEY not found. Using PyPDF fallback for PDF parsing."
            )

    async def parse(self, file_path: str) -> str:
        """
        Parses a PDF file and returns the extracted text.
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return ""

        if self.use_llama:
            return await self._parse_with_llama(file_path)
        else:
            return await self._parse_with_pypdf(file_path)

    async def _parse_with_llama(self, file_path: str) -> str:
        try:
            from llama_parse import LlamaParse

            parser = LlamaParse(
                api_key=self.llama_api_key, result_type="markdown", verbose=True
            )

            # LlamaParse is typically synchronous or has its own async methods.
            # We'll run it in a thread if it's blocking, but for now let's assume direct call.
            # LlamaParse.load_data() returns a list of Document objects.

            documents = parser.load_data(file_path)
            text = "\n\n".join([doc.text for doc in documents])
            return text

        except Exception as e:
            logger.error(f"LlamaParse failed: {e}. Falling back to PyPDF.")
            return await self._parse_with_pypdf(file_path)

    async def _parse_with_pypdf(self, file_path: str) -> str:
        try:
            import pypdf

            text = ""
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"

            return text
        except Exception as e:
            logger.error(f"PyPDF failed: {e}")
            return ""
