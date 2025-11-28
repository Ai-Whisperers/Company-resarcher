import streamlit as st
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.pipeline.orchestrator import PipelineOrchestrator

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
        orchestrator = PipelineOrchestrator()

        # We can't easily stream logs to Streamlit without a custom handler,
        # so we'll just await the result for now.
        with st.spinner("Pipeline is working... (This may take 2-3 minutes)"):
            final_state = await orchestrator.conduct_research(
                company_name=company_name,
                url=url,
                industry=industry,
            )
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

        # Helper to get content safely from pipeline results
        def get_phase_content(phase_name_partial):
            if not final_state or "phases" not in final_state:
                return "No data."
            for phase in final_state["phases"]:
                if phase_name_partial.lower() in phase.get("phase_name", "").lower():
                    return phase.get("markdown_content", "No content generated.")
            return "No content generated."

        # Build executive summary from all phases
        def get_executive_summary():
            if not final_state or "phases" not in final_state:
                return "No report generated."
            summary_parts = [f"# Research Report: {final_state.get('company_name', 'Unknown')}\n"]
            for phase in final_state["phases"]:
                summary_parts.append(f"## {phase.get('phase_name', 'Unknown Phase')}\n")
                content = phase.get("markdown_content", "")
                # Take first 500 chars as summary
                if len(content) > 500:
                    summary_parts.append(content[:500] + "...\n")
                else:
                    summary_parts.append(content + "\n")
            return "\n".join(summary_parts)

        with tab1:
            st.markdown(get_executive_summary())

        with tab2:
            st.markdown(get_phase_content("financial"))

        with tab3:
            st.markdown(get_phase_content("market"))

        with tab4:
            st.markdown(get_phase_content("competitor"))

        with tab5:
            st.markdown(get_phase_content("brand"))

        with tab6:
            st.markdown(get_phase_content("sales"))

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
