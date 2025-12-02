# Research Targets

This folder contains company profiles for batch research. Each YAML file defines a company to research, and related companies can be grouped together for comparative analysis.

## Folder Structure

```
research_targets/
  README.md                    # This file
  paraguay_telecom/            # Market segment folder
    _market.yaml               # Market-level configuration
    personal_paraguay.yaml     # Primary target company
    tigo_paraguay.yaml         # Competitor
    claro_paraguay.yaml        # Competitor
    telecom_argentina.yaml     # Parent company
```

## Usage

### Research a single company:
```bash
python main.py --profile research_targets/paraguay_telecom/personal_paraguay.yaml
```

### Research all companies in a market segment:
```bash
python main.py --batch research_targets/paraguay_telecom/
```

### Research with market context:
```bash
python main.py --market research_targets/paraguay_telecom/
```

## Profile Format

Each company profile is a YAML file with the following structure:

```yaml
name: "Company Name"
website: "https://company.com"
industry: "Industry Name"
country: "Country"
# Optional fields
parent_company: "Parent Corp"
competitors:
  - "Competitor 1"
  - "Competitor 2"
research_focus:
  - market
  - financial
  - competitor
  - brand
  - sales
notes: "Any special research notes"
```
