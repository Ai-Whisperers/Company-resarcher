from typing import List, Dict

PRODUCTS = [
    {
        "name": "AI Automation Suite",
        "description": "A comprehensive platform for automating business processes using AI agents.",
        "benefits": [
            "Reduce operational costs",
            "Increase efficiency",
            "24/7 availability",
        ],
        "ideal_customer": "Companies with high manual data entry or customer support volume.",
    },
    {
        "name": "Cloud Infrastructure Optimizer",
        "description": "AI-driven tool to analyze and reduce cloud spend on AWS/Azure/GCP.",
        "benefits": ["Cost reduction", "Performance tuning", "Security compliance"],
        "ideal_customer": "Tech-heavy companies with large cloud bills.",
    },
    {
        "name": "Data Analytics Dashboard",
        "description": "Real-time business intelligence dashboard with predictive analytics.",
        "benefits": ["Data-driven decisions", "Visual insights", "Trend forecasting"],
        "ideal_customer": "Retail, Finance, or Logistics companies needing visibility.",
    },
    {
        "name": "Cybersecurity Sentinel",
        "description": "Advanced threat detection system using machine learning.",
        "benefits": [
            "Proactive protection",
            "Real-time alerts",
            "Compliance reporting",
        ],
        "ideal_customer": "Financial services, Healthcare, or Enterprise.",
    },
]


def get_product_portfolio() -> List[Dict[str, str]]:
    return PRODUCTS
