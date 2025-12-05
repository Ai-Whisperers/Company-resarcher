"""
Quick test if Phoenix is installed and working.
Run this before starting the full Phoenix setup.
"""
import sys

print("="*60)
print("Phoenix Installation Check")
print("="*60)

# Check Phoenix
print("\n1. Checking Phoenix...")
try:
    import phoenix as px
    print("   ✓ Phoenix installed:", px.__version__)
except ImportError:
    print("   ✗ Phoenix not installed")
    print("   Install: pip install arize-phoenix")
    sys.exit(1)

# Check OpenInference
print("\n2. Checking OpenInference instrumentation...")
try:
    from openinference.instrumentation.langchain import LangChainInstrumentor
    print("   ✓ OpenInference installed")
except ImportError:
    print("   ✗ OpenInference not installed")
    print("   Install: pip install openinference-instrumentation-langchain")
    sys.exit(1)

# Check LangChain
print("\n3. Checking LangChain...")
try:
    from langchain_core.messages import HumanMessage
    print("   ✓ LangChain installed")
except ImportError:
    print("   ✗ LangChain not installed")
    print("   Install: pip install langchain-core")
    sys.exit(1)

print("\n" + "="*60)
print("SUCCESS! All dependencies installed.")
print("="*60)
print("\nNext step:")
print("  python start_phoenix.py")
print("\nOr read the guide:")
print("  cat QUICK_START_TRACING.md")
