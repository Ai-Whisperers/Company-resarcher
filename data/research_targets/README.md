# Research Targets

This folder contains company profiles for batch research. Each YAML file defines a company to research, and related companies can be grouped together for comparative analysis.

## Folder Structure

```
research_targets/
  README.md                          # This file

  paraguay_telecom/                  # Telecommunications market
    _market.yaml                     # Market-level configuration
    personal_paraguay.yaml           # Primary target company
    tigo_paraguay.yaml               # Competitor
    claro_paraguay.yaml              # Competitor
    copaco.yaml                      # State-owned competitor
    vox_paraguay.yaml                # MVNO
    telecom_argentina.yaml           # Parent company

  paraguay_biotech/                  # Biotech & diagnostics market
    _market.yaml                     # Market-level configuration
    meyerlab.yaml                    # Primary target (molecular biology)
    laboratorio_san_roque.yaml       # Competitor (comprehensive diagnostics)
    laboratorio_curie.yaml           # Competitor (cancer genomics/NGS)
    lac_paraguay.yaml                # Competitor (high-complexity services)
    iics_asuncion.yaml               # Academic/public institution
```

## Usage

### Research a single company:
```bash
# Telecommunications
python main.py --profile research_targets/paraguay_telecom/personal_paraguay.yaml

# Biotech/Diagnostics
python main.py --profile research_targets/paraguay_biotech/meyerlab.yaml
```

### Research all companies in a market segment:
```bash
# Telecom market (all companies)
python main.py --batch research_targets/paraguay_telecom/

# Biotech market (all companies)
python main.py --batch research_targets/paraguay_biotech/

# With delay between companies (recommended)
python main.py --batch research_targets/paraguay_biotech/ --delay 30
```

### Research with market context:
```bash
python main.py --market research_targets/paraguay_telecom/
python main.py --market research_targets/paraguay_biotech/
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
