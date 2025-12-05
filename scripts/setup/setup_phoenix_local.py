"""
Setup Phoenix by Arize for local LangChain tracing.
100% free, runs locally, no cloud required.

Install: pip install arize-phoenix openinference-instrumentation-langchain

Usage:
    python setup_phoenix_local.py
    # Then run your research - traces will appear at http://localhost:6006
"""
import phoenix as px
from phoenix.otel import register

# Launch Phoenix locally
session = px.launch_app()
print(f"Phoenix UI: {session.url}")

# Setup OpenTelemetry instrumentation for LangChain
tracer_provider = register(
    project_name="company-researcher",
    endpoint="http://localhost:6006/v1/traces",
)

# Instrument LangChain
from openinference.instrumentation.langchain import LangChainInstrumentor
LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

print("\n" + "="*60)
print("Phoenix Tracing Started!")
print("="*60)
print(f"\n📊 Dashboard: {session.url}")
print("\nNow run your research:")
print("  python main.py --name 'Tesla' --industry 'Automotive'")
print("\nAll traces will appear in the Phoenix UI!")
print("="*60)

# Keep Phoenix running
print("\nPress Ctrl+C to stop Phoenix")
try:
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping Phoenix...")
