from typing import Dict, Any, Optional, List
import os
from ..core.logger import setup_logger

logger = setup_logger("sec_tool")


class SECTool:
    """
    Tool for analyzing SEC filings using edgartools.
    Supports both ticker symbols and company name lookups.
    """

    def __init__(self):
        # edgartools doesn't strictly require an API key for basic usage,
        # but it's good practice to set a user agent.
        self.identity = os.getenv(
            "SEC_IDENTITY", "Company Researcher Agent (research@example.com)"
        )

        # Initialize edgartools identity
        from edgartools import set_identity

        set_identity(self.identity)

        # Cache for company name to ticker lookups
        self._ticker_cache: Dict[str, Optional[str]] = {}

    def find_ticker(self, company_name: str) -> Optional[str]:
        """
        Find ticker symbol for a company name using SEC EDGAR search.

        Args:
            company_name: Company name to search for (e.g., "Apple", "Nestle")

        Returns:
            Ticker symbol if found, None otherwise
        """
        # Check cache first
        cache_key = company_name.lower().strip()
        if cache_key in self._ticker_cache:
            return self._ticker_cache[cache_key]

        try:
            from edgartools import find_company

            # Search for the company
            results = find_company(company_name)

            if results and len(results) > 0:
                # Get the first (best) match
                ticker = results[0].tickers[0] if results[0].tickers else None
                self._ticker_cache[cache_key] = ticker
                logger.info(f"Found ticker '{ticker}' for company '{company_name}'")
                return ticker

            logger.warning(f"No ticker found for company: {company_name}")
            self._ticker_cache[cache_key] = None
            return None

        except Exception as e:
            logger.error(f"Failed to find ticker for {company_name}: {e}")
            self._ticker_cache[cache_key] = None
            return None

    def get_company_filings(
        self, ticker_or_name: str, form_type: str = "10-K", limit: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Fetches recent filings for a company.

        Args:
            ticker_or_name: Either a ticker symbol (e.g., "AAPL") or company name (e.g., "Apple")
            form_type: SEC form type (default: "10-K")
            limit: Number of filings to retrieve
        """
        # Try to determine if input is a ticker or company name
        ticker = ticker_or_name.upper()

        # If it looks like a company name (contains spaces or is long), search for ticker
        if " " in ticker_or_name or len(ticker_or_name) > 5:
            found_ticker = self.find_ticker(ticker_or_name)
            if found_ticker:
                ticker = found_ticker
            else:
                logger.warning(f"Could not find ticker for '{ticker_or_name}', trying as-is")

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
                    }
                )
            return results
        except Exception as e:
            logger.error(f"Failed to get filings for {ticker}: {e}")
            return []

    def get_latest_10k_content(self, ticker_or_name: str) -> str:
        """
        Fetches the text content of the latest 10-K.

        Args:
            ticker_or_name: Either a ticker symbol (e.g., "AAPL") or company name (e.g., "Apple")
        """
        # Try to determine if input is a ticker or company name
        ticker = ticker_or_name.upper()

        # If it looks like a company name, search for ticker
        if " " in ticker_or_name or len(ticker_or_name) > 5:
            found_ticker = self.find_ticker(ticker_or_name)
            if found_ticker:
                ticker = found_ticker
            else:
                logger.warning(f"Could not find ticker for '{ticker_or_name}', trying as-is")

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
