"""
Start Phoenix for local LangChain tracing.

Phoenix is 100% free and open source - no cloud required!

Install: pip install arize-phoenix openinference-instrumentation-langchain

Usage:
    1. python start_phoenix.py
    2. Open http://localhost:6006 in browser
    3. In another terminal: python main.py --name "Tesla" --industry "Automotive"
    4. Watch traces appear in real-time!
"""
import sys

try:
    import phoenix as px
    from phoenix.otel import register
    from openinference.instrumentation.langchain import LangChainInstrumentor
except ImportError:
    print("="*60)
    print("ERROR: Phoenix not installed")
    print("="*60)
    print("\nInstall with:")
    print("  pip install arize-phoenix openinference-instrumentation-langchain")
    sys.exit(1)

print("="*60)
print("Starting Phoenix - Local LangChain Tracing")
print("="*60)

# Launch Phoenix UI
print("\n1. Launching Phoenix UI...")
session = px.launch_app()
print(f"   Phoenix UI: {session.url}")

# Setup OpenTelemetry tracing
print("\n2. Configuring tracing...")
tracer = register(
    project_name="company-researcher",
    endpoint=f"{session.url}/v1/traces"
)

# Instrument LangChain (automatic tracing)
print("\n3. Instrumenting LangChain...")
LangChainInstrumentor().instrument(tracer_provider=tracer)

print("\n" + "="*60)
print("SUCCESS! Phoenix is Running")
print("="*60)
print(f"\nDashboard: {session.url}")
print("\nWhat to do next:")
print("  1. Keep this terminal open (Phoenix is running)")
print("  2. Open a NEW terminal")
print("  3. Run: python main.py --name 'Tesla' --industry 'Automotive'")
print("  4. Watch traces appear in the Phoenix dashboard!")
print("\nFeatures:")
print("  - Real-time trace streaming")
print("  - Complete execution trees")
print("  - LLM prompts & responses")
print("  - Token usage & costs")
print("  - Error tracking")
print("  - Timeline visualization")
print("\n" + "="*60)
print("Press Ctrl+C to stop Phoenix")
print("="*60)

# Keep Phoenix running
try:
    import time
    print("\nWaiting for traces...")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\nStopping Phoenix...")
    print("Thanks for using Phoenix! 🎉")
