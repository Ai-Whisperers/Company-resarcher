# Key Metrics

## Financial Metrics
| Metric | Value | Trend |
|--------|-------|-------|
| Revenue | {{ revenue | default("N/A") }} | {{ revenue_trend | default("N/A") }} |
| ARPU | {{ arpu | default("N/A") }} | {{ arpu_trend | default("N/A") }} |
| CAC | {{ cac | default("N/A") }} | {{ cac_trend | default("N/A") }} |
| LTV | {{ ltv | default("N/A") }} | {{ ltv_trend | default("N/A") }} |
| LTV:CAC Ratio | {{ ltv_cac_ratio | default("N/A") }} | {{ ltv_cac_trend | default("N/A") }} |

## Operational Metrics
| Metric | Value |
|--------|-------|
| Monthly Active Users | {{ mau | default("N/A") }} |
| Churn Rate | {{ churn_rate | default("N/A") }} |
| Net Promoter Score | {{ nps | default("N/A") }} |
| Employee Count | {{ employee_count | default("N/A") }} |

## Growth Metrics
{{ growth_metrics | default("N/A") }}

---
*Generated: {{ generated_at | format_date }}*
