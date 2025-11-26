# Agentic System Vision

**Objective**: Build an autonomous, self-correcting research system capable of generating deep, evidence-based company and sector intelligence.

## 🧠 Core Philosophy

1.  **Specialization**: We don't ask one LLM to do everything. We have a "Financial Analyst", a "Market Researcher", and a "Sales Strategist".
2.  **Evidence-First**: No claim without a source. The system must gather raw data _before_ attempting any analysis.
3.  **Dynamic & Self-Correcting**: The system is not a linear pipe. It loops back if data is missing ("Gap Fill") and challenges its own logic ("Devil's Advocate").
4.  **Sector-Aware**: We don't just look at one company in a vacuum. We use a shared "Vault" to understand the broader ecosystem and trends.

## 👥 The "Research Team" Metaphor

Instead of a single prompt, we simulate a corporate structure:

- **The Manager (Orchestrator)**: Plans the research, assigns tasks, manages the budget, and tracks progress.
- **The Scouts (Researchers)**: Go out to the web (Browser/Search) and bring back raw data.
- **The Analysts (Reasoning)**: Read the raw data and calculate metrics.
- **The Critic (Logic)**: Challenges the Analysts' conclusions to ensure robustness.
- **The Writers (Content)**: Draft the final reports in specific markdown formats.
- **The Editor (Reviewer)**: Checks every claim against the source log.
- **The Sector Analyst (Meta)**: Connects the dots across multiple companies.

## 🌊 The 4-Wave Approach (Cyclic)

To ensure data integrity, we split execution into distinct waves, but allow for feedback loops.

1.  **Gathering Wave**: Pure data collection. Checks "The Vault" first.
2.  **Thinking Wave**: Analysis + Logic Checking. Can trigger a "Gap Fill" loop back to Wave 1.
3.  **Writing Wave**: Drafting the content based on the verified analysis.
4.  **Review Wave**: Verifying citations and quality.
5.  **Meta-Wave**: Updating the Sector Knowledge Graph.

## 🏆 Success Criteria

- **Scalability**: Adding a "Legal Agent" shouldn't break the "Sales Agent".
- **Traceability**: Every sentence in the final report must link to a row in the Source Log.
- **Robustness**: The system self-corrects when data is missing or logic is flawed.
- **Efficiency**: It doesn't re-scrape data we already have in The Vault.
