# Valuation Assessment

## Current Valuation
{{ current_valuation | default("N/A") }}

## Valuation Methods

### Comparable Company Analysis
{{ comparable_analysis | default("N/A") }}

### DCF Analysis
{{ dcf_analysis | default("N/A") }}

### Precedent Transactions
{{ precedent_transactions | default("N/A") }}

## Key Multiples
| Multiple | Value | Industry Avg |
|----------|-------|--------------|
| P/E | {{ pe_ratio | default("N/A") }} | {{ pe_industry | default("N/A") }} |
| P/S | {{ ps_ratio | default("N/A") }} | {{ ps_industry | default("N/A") }} |
| EV/EBITDA | {{ ev_ebitda | default("N/A") }} | {{ ev_ebitda_industry | default("N/A") }} |

## Valuation Summary
{{ valuation_summary | default("N/A") }}

---
*Generated: {{ generated_at | format_date }}*
