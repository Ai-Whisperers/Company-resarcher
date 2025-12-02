"""
Company Researcher Streamlit UI.

Features:
- Research company profiles with AI agents
- Session state for research history
- Error handling with retry capability
- Export functionality
"""

import streamlit as st
import asyncio
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.pipeline.orchestrator import PipelineOrchestrator

# Page configuration
st.set_page_config(
    page_title="Company Researcher Agent",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# Session State Initialization (UI-002)
# =============================================================================

if "research_history" not in st.session_state:
    st.session_state.research_history = []

if "current_result" not in st.session_state:
    st.session_state.current_result = None

if "last_error" not in st.session_state:
    st.session_state.last_error = None

if "preferences" not in st.session_state:
    st.session_state.preferences = {
        "default_country": "USA",
        "show_raw_output": False,
        "dark_mode": True,  # UX-002: Dark mode enabled by default
    }

# UX-002: Dark mode CSS injection for custom styling
DARK_MODE_CSS = """
<style>
    /* Dark mode custom styles */
    .stApp {
        transition: background-color 0.3s ease;
    }

    /* Improve code block visibility in dark mode */
    .stCodeBlock {
        background-color: #1e1e1e !important;
    }

    /* Better table styling */
    .stTable {
        background-color: #262730 !important;
    }

    /* Card-like styling for metrics */
    [data-testid="metric-container"] {
        background-color: #262730;
        border-radius: 8px;
        padding: 10px;
    }
</style>
"""

LIGHT_MODE_CSS = """
<style>
    /* Light mode custom styles */
    .stApp {
        transition: background-color 0.3s ease;
    }

    /* Card-like styling for metrics */
    [data-testid="metric-container"] {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 10px;
    }
</style>
"""

def apply_theme():
    """Apply custom theme CSS based on preference (UX-002)."""
    if st.session_state.preferences.get("dark_mode", True):
        st.markdown(DARK_MODE_CSS, unsafe_allow_html=True)
    else:
        st.markdown(LIGHT_MODE_CSS, unsafe_allow_html=True)


# =============================================================================
# Helper Functions
# =============================================================================


def add_to_history(company_name: str, result: dict, success: bool):
    """Add research result to session history."""
    st.session_state.research_history.append({
        "company_name": company_name,
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "result": result if success else None,
    })
    # Keep only last 10 entries
    if len(st.session_state.research_history) > 10:
        st.session_state.research_history = st.session_state.research_history[-10:]


def get_phase_content(final_state: dict, phase_name_partial: str) -> str:
    """Safely extract content for a specific phase."""
    if not final_state or "phases" not in final_state:
        return "No data available."
    for phase in final_state["phases"]:
        if phase_name_partial.lower() in phase.get("phase_name", "").lower():
            return phase.get("markdown_content", "No content generated.")
    return "No content generated for this phase."


def get_executive_summary(final_state: dict) -> str:
    """Build executive summary from all phases."""
    if not final_state or "phases" not in final_state:
        return "No report generated."

    summary_parts = [f"# Research Report: {final_state.get('company_name', 'Unknown')}\n"]
    summary_parts.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n")

    for phase in final_state["phases"]:
        summary_parts.append(f"## {phase.get('phase_name', 'Unknown Phase')}\n")
        content = phase.get("markdown_content", "")
        # Take first 500 chars as summary
        if len(content) > 500:
            summary_parts.append(content[:500] + "...\n\n")
        else:
            summary_parts.append(content + "\n\n")
    return "\n".join(summary_parts)


def export_report(final_state: dict, format: str = "markdown") -> str:
    """Export report in specified format."""
    if format == "markdown":
        return get_executive_summary(final_state)
    elif format == "json":
        return json.dumps(final_state, indent=2, default=str)
    return ""


def classify_error(error: Exception) -> tuple:
    """Classify error and return (type, message, is_retryable)."""
    error_str = str(error).lower()

    if "timeout" in error_str or "timed out" in error_str:
        return (
            "timeout",
            "The request timed out. The AI services may be slow or overloaded.",
            True,
        )
    elif "rate limit" in error_str or "429" in error_str:
        return (
            "rate_limit",
            "Rate limit reached. Please wait a moment before retrying.",
            True,
        )
    elif "api key" in error_str or "authentication" in error_str:
        return (
            "auth",
            "API key error. Please check your configuration.",
            False,
        )
    elif "network" in error_str or "connection" in error_str:
        return (
            "network",
            "Network error. Please check your internet connection.",
            True,
        )
    else:
        return (
            "unknown",
            f"An unexpected error occurred: {error}",
            True,
        )


# =============================================================================
# Main UI
# =============================================================================

st.title("🕵️‍♂️ Company Researcher Agent")
st.markdown("---")

# Sidebar for inputs
with st.sidebar:
    st.header("🎯 Target Company")

    company_name = st.text_input(
        "Company Name",
        placeholder="e.g. Nvidia",
        help="Enter the company name to research",
    )
    url = st.text_input(
        "Website URL",
        placeholder="e.g. https://nvidia.com",
        help="Optional: Company website for more accurate results",
    )
    industry = st.text_input(
        "Industry",
        placeholder="e.g. Technology",
        help="Optional: Industry sector",
    )
    country = st.text_input(
        "Country",
        value=st.session_state.preferences.get("default_country", "USA"),
        help="Country for region-specific results",
    )

    st.markdown("---")
    start_btn = st.button("🚀 Start Research", type="primary", use_container_width=True)

    # Research History (UI-002)
    st.markdown("---")
    st.header("📜 Research History")

    if st.session_state.research_history:
        for i, entry in enumerate(reversed(st.session_state.research_history[-5:])):
            status_icon = "✅" if entry["success"] else "❌"
            with st.expander(f"{status_icon} {entry['company_name']}", expanded=False):
                st.caption(entry["timestamp"][:16])
                if entry["success"] and entry["result"]:
                    if st.button(f"View", key=f"view_{i}"):
                        st.session_state.current_result = entry["result"]
                        st.rerun()
    else:
        st.caption("No research history yet.")

    # Preferences (UI-002)
    st.markdown("---")
    with st.expander("⚙️ Preferences"):
        st.session_state.preferences["default_country"] = st.text_input(
            "Default Country",
            value=st.session_state.preferences.get("default_country", "USA"),
            key="pref_country",
        )
        st.session_state.preferences["show_raw_output"] = st.checkbox(
            "Show Raw Output",
            value=st.session_state.preferences.get("show_raw_output", False),
        )
        # UX-002: Dark mode toggle
        st.session_state.preferences["dark_mode"] = st.checkbox(
            "🌙 Dark Mode",
            value=st.session_state.preferences.get("dark_mode", True),
            help="Toggle between dark and light theme",
        )

# Apply theme based on preference (UX-002)
apply_theme()


# Main content area
if start_btn and company_name:
    st.session_state.last_error = None
    st.session_state.current_result = None

    # Progress container with stages (UI-001)
    progress_placeholder = st.empty()
    status_placeholder = st.empty()

    async def run_research():
        orchestrator = PipelineOrchestrator()
        final_state = await orchestrator.conduct_research(
            company_name=company_name,
            url=url,
            industry=industry,
        )
        return final_state

    # Run async loop with timeout handling (UI-001)
    try:
        with progress_placeholder.container():
            st.info(f"🔍 Starting research for **{company_name}**...")

            # Progress bar simulation
            progress_bar = st.progress(0, text="Initializing...")

            # Update progress stages
            stages = [
                (10, "Gathering company information..."),
                (30, "Analyzing financial data..."),
                (50, "Researching market position..."),
                (70, "Analyzing competitors..."),
                (85, "Generating insights..."),
                (95, "Compiling final report..."),
            ]

            # Start research with visual progress
            with st.spinner("Pipeline is working... (This may take 2-3 minutes)"):
                # Create event loop for async
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    # Run with timeout
                    final_state = loop.run_until_complete(
                        asyncio.wait_for(run_research(), timeout=300)  # 5 min timeout
                    )
                finally:
                    loop.close()

        progress_placeholder.empty()

        # Success! Store result and add to history
        st.session_state.current_result = final_state
        add_to_history(company_name, final_state, success=True)

        st.success("✅ Research Complete!")
        st.balloons()

    except asyncio.TimeoutError:
        progress_placeholder.empty()
        error_type, message, retryable = classify_error(Exception("timeout"))
        st.session_state.last_error = {"type": error_type, "message": message, "retryable": retryable}
        add_to_history(company_name, None, success=False)

    except Exception as e:
        progress_placeholder.empty()
        error_type, message, retryable = classify_error(e)
        st.session_state.last_error = {"type": error_type, "message": message, "retryable": retryable}
        add_to_history(company_name, None, success=False)

# Display error with retry option (UI-001)
if st.session_state.last_error:
    error = st.session_state.last_error

    if error["type"] == "timeout":
        st.error(f"⏱️ **Timeout Error**\n\n{error['message']}")
    elif error["type"] == "rate_limit":
        st.warning(f"🚦 **Rate Limited**\n\n{error['message']}")
    elif error["type"] == "auth":
        st.error(f"🔐 **Authentication Error**\n\n{error['message']}")
    elif error["type"] == "network":
        st.error(f"🌐 **Network Error**\n\n{error['message']}")
    else:
        st.error(f"❌ **Error**\n\n{error['message']}")

    if error["retryable"]:
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 Retry", type="primary"):
                st.session_state.last_error = None
                st.rerun()

# Display results
if st.session_state.current_result:
    final_state = st.session_state.current_result

    # Export options (UI-002)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        st.download_button(
            "📥 Export Markdown",
            data=export_report(final_state, "markdown"),
            file_name=f"{final_state.get('company_name', 'report')}_research.md",
            mime="text/markdown",
        )
    with col3:
        st.download_button(
            "📥 Export JSON",
            data=export_report(final_state, "json"),
            file_name=f"{final_state.get('company_name', 'report')}_research.json",
            mime="application/json",
        )

    # Display Results using Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Executive Summary",
        "💰 Financials",
        "📈 Market",
        "🎯 Competitors",
        "🏷️ Brand",
        "💼 Sales Strategy",
    ])

    with tab1:
        st.markdown(get_executive_summary(final_state))

    with tab2:
        st.markdown(get_phase_content(final_state, "financial"))

    with tab3:
        st.markdown(get_phase_content(final_state, "market"))

    with tab4:
        st.markdown(get_phase_content(final_state, "competitor"))

    with tab5:
        st.markdown(get_phase_content(final_state, "brand"))

    with tab6:
        st.markdown(get_phase_content(final_state, "sales"))

    # Raw output option (UI-002)
    if st.session_state.preferences.get("show_raw_output"):
        with st.expander("🔧 Raw Output"):
            st.json(final_state)

elif not start_btn or not company_name:
    if start_btn and not company_name:
        st.warning("⚠️ Please enter a company name.")
    else:
        st.info("👈 Enter company details in the sidebar to begin research.")

        # Vault Explorer
        st.markdown("### 📂 Research Vault")
        st.markdown("Recent reports stored in the system:")

        vault_path = Path("data/vault")
        if vault_path.exists():
            files = sorted(vault_path.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
            if files:
                for f in files[:10]:  # Show last 10
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(f"📄 {f.name}")
                    with col2:
                        st.caption(datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d"))
            else:
                st.caption("No files in Vault.")
        else:
            st.caption("Vault directory not found.")

# Footer
st.markdown("---")
st.caption("Company Researcher Agent v2.0 | Powered by AI")
