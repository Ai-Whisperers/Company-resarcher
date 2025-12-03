import asyncio
import os
from src.tools.data.content.pdf_parser import PDFParser


async def main():
    print("Testing PDF Parser...")
    parser = PDFParser()

    if parser.use_llama:
        print("Using LlamaParse (API Key found)")
    else:
        print("Using PyPDF (Fallback)")

    # Create a dummy PDF file for testing
    # For now, we just check if the class instantiates without error
    # and if the fallback logic works.

    print("PDF Parser initialized successfully.")


if __name__ == "__main__":
    asyncio.run(main())
