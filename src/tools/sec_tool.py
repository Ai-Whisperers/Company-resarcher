from typing import Dict, Any, Optional, List
import os
from ..core.logger import setup_logger

logger = setup_logger("sec_tool")


class SECTool:
    """
    Tool for analyzing SEC filings using edgartools.
    """

    def __init__(self):
        # edgartools doesn't strictly require an API key for basic usage,
        # but it's good practice to set a user agent.
        # We'll assume the environment might have one, or we default.
        self.identity = os.getenv(
            "SEC_IDENTITY", "Company Researcher Agent (research@example.com)"
        )

        # Initialize client if library supports it directly,
        # but edgartools is often functional-based or requires set_identity.
        from edgartools import set_identity

        set_identity(self.identity)

    def get_company_filings(
        self, ticker: str, form_type: str = "10-K", limit: int = 1
    ) -> List[Dict[str, Any]]:
        """Fetches recent filings for a company."""
        try:
            from edgartools import Company

            company = Company(ticker)
            filings = company.get_filings(form=form_type).latest(limit)

            results = []
            # Handle single result or list
            if limit == 1 and filings:
                filings = [filings]
            elif not filings:
                return []

            for filing in filings:
                results.append(
                    {
                        "accession_number": filing.accession_number,
                        "filing_date": str(filing.filing_date),
                        "form": filing.form,
                        "url": filing.url,
                        # We can try to get the text or html content if needed
                        # "content": filing.text()[:5000] # Truncate for safety
                    }
                )
            return results
        except Exception as e:
            logger.error(f"Failed to get filings for {ticker}: {e}")
            return []

    def get_latest_10k_content(self, ticker: str) -> str:
        """Fetches the text content of the latest 10-K."""
        try:
            from edgartools import Company

            company = Company(ticker)
            filing = company.get_filings(form="10-K").latest()
            if filing:
                return filing.text()
            return ""
        except Exception as e:
            logger.error(f"Failed to get 10-K for {ticker}: {e}")
            return ""
