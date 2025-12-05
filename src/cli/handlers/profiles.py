import yaml
from pathlib import Path
from typing import Dict, List, Any
from src.core.logging import setup_logger

logger = setup_logger("cli.handlers.profiles")


def load_company_profile(profile_path: str) -> Dict[str, Any]:
    """
    Load a company profile from a YAML file.

    Args:
        profile_path: Path to the YAML profile file

    Returns:
        Dictionary with company configuration
    """
    path = Path(profile_path)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Extract company info from nested structure
    company = data.get("company", data)

    # Extract ticker info (INT-002: Alpha Vantage integration)
    # Support both flat and nested ownership structures
    ticker = company.get("ticker")
    exchange = company.get("exchange")
    parent_ticker = company.get("parent_ticker")
    parent_company = company.get("parent_company")

    # Check nested ownership structure (e.g., ownership.adr: "NYSE: TEO")
    ownership = company.get("ownership", {})
    if not ticker and ownership:
        # Try to extract from ADR or ticker field
        adr = ownership.get("adr", "")
        if adr and ": " in adr:
            # Parse "NYSE: TEO" format
            parts = adr.split(": ")
            if len(parts) == 2:
                exchange = exchange or parts[0]
                ticker = ticker or parts[1]
        if not ticker:
            ticker = ownership.get("ticker")
        if not exchange:
            exchange = ownership.get("stock_exchange")

    return {
        "name": company.get("name", path.stem),
        "website": company.get("website", ""),
        "industry": company.get("industry", ""),
        "country": company.get("country", "Global"),
        "research_focus": data.get("research", {}).get(
            "focus_areas", ["market", "financial", "competitor", "brand", "sales"]
        ),
        "priority_queries": data.get("research", {}).get("priority_queries", []),
        "notes": data.get("notes", ""),
        # INT-002: Stock ticker fields
        "ticker": ticker,
        "exchange": exchange,
        "parent_ticker": parent_ticker,
        "parent_company": parent_company,
    }


def load_batch_profiles(batch_path: str) -> List[Dict[str, Any]]:
    """
    Load all company profiles from a market folder.

    Args:
        batch_path: Path to the market folder containing YAML files

    Returns:
        List of company configurations
    """
    path = Path(batch_path)
    if not path.exists():
        raise FileNotFoundError(f"Batch folder not found: {batch_path}")

    profiles = []

    # Load all YAML files except _market.yaml (market config)
    for yaml_file in sorted(path.glob("*.yaml")):
        if yaml_file.name.startswith("_"):
            continue  # Skip market config files

        try:
            profile = load_company_profile(str(yaml_file))
            profile["_source_file"] = str(yaml_file)
            profiles.append(profile)
            logger.info(f"Loaded profile: {profile['name']}")
        except Exception as e:
            logger.warning(f"Failed to load {yaml_file}: {e}")

    return profiles
