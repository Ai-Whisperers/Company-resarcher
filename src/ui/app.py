import streamlit as st
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.agents.orchestrator import ResearchOrchestrator
from src.core.types import CompanyProfile

st.set_page_config(page_title="Company Researcher Agent", page_icon="🕵️‍♂️", layout="wide")

st.title("🕵️‍♂️ Company Researcher Agent")
st.markdown("---")

# Sidebar for inputs
with st.sidebar:
    st.header("Target Company")
    company_name = st.text_input("Company Name", placeholder="e.g. Nvidia")
    url = st.text_input("Website URL", placeholder="e.g. https://nvidia.com")
    industry = st.text_input("Industry", placeholder="e.g. Technology")
    country = st.text_input("Country", value="USA")

    start_btn = st.button("Start Research", type="primary")

# Main content area
if start_btn and company_name:
    st.info(f"Starting research for **{company_name}**...")

    # Progress container
    progress_container = st.container()

    async def run_research():
        orchestrator = ResearchOrchestrator()
        company = CompanyProfile(
            name=company_name, website=url, industry=industry, country=country
        )

        # We can't easily stream logs to Streamlit without a custom handler,
        # so we'll just await the result for now.
        with st.spinner("Agents are working... (This may take 2-3 minutes)"):
            final_state = await orchestrator.conduct_research(company)
            return final_state

    # Run async loop
    try:
        final_state = asyncio.run(run_research())

        st.success("Research Complete!")

        # Display Results using Tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            [
                "Executive Summary",
                "Financials",
                "Market",
                "Competitors",
                "Brand",
                "Sales Strategy",
            ]
        )

        # Helper to get content safely
        def get_content(phase_name):
            if not final_state or "research_results" not in final_state:
                return "No data."
            return (
                final_state["research_results"]
                .get(phase_name, {})
                .get("markdown_content", "No content generated.")
            )

        with tab1:
            st.markdown(final_state.get("final_report", "No report generated."))

        with tab2:
            st.markdown(get_content("Financial Analysis"))

        with tab3:
            st.markdown(get_content("Market Intelligence"))

        with tab4:
            st.markdown(get_content("Competitive Landscape"))

        with tab5:
            st.markdown(get_content("Brand Strategy"))

        with tab6:
            st.markdown(get_content("Sales Strategy"))

    except Exception as e:
        st.error(f"An error occurred: {e}")

elif start_btn and not company_name:
    st.warning("Please enter a company name.")

else:
    st.info("Enter company details in the sidebar to begin.")

    # Vault Explorer (Simple Mockup)
    st.markdown("### 📂 Vault Explorer")
    st.markdown("Recent reports stored in the system:")

    # In a real app, we'd list files from data/vault
    import os

    vault_path = "data/vault"
    if os.path.exists(vault_path):
        files = os.listdir(vault_path)
        if files:
            for f in files:
                st.text(f"📄 {f}")
        else:
            st.text("No files in Vault.")
    else:
        st.text("Vault directory not found.")
