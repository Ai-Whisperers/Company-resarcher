# TE-022: No Fuzz Testing

**Priority**: Medium
**Category**: Testing
**Status**: Open
**Estimated Effort**: Medium

## Description

No fuzz testing is performed to discover crashes, hangs, or security vulnerabilities with random/malformed inputs. Fuzzing is particularly important for input parsing and external data handling.

## Current State

- No fuzz testing infrastructure
- Input parsers not stress-tested
- External data handling not fuzzed
- No crash/hang detection

## Fuzz Testing Targets

| Component | Input Type | Risk |
|-----------|------------|------|
| PDF Parser | Binary PDF data | Crash, memory corruption |
| HTML Parser | Malformed HTML | Crash, DoS |
| URL Parser | Malformed URLs | Security bypass |
| JSON Parser | Malformed JSON | Crash, injection |
| Company Name | Unicode/special chars | XSS, path traversal |

## Impact

- **Crashes in production**: Malformed input causes failures
- **Security vulnerabilities**: Fuzzing finds injection points
- **DoS vectors**: Inputs that cause hangs
- **Data corruption**: Edge cases corrupt state

## Proposed Solution

1. **Install atheris (Google's Python fuzzer)**:

   ```bash
   pip install atheris
   ```

2. **Create fuzz tests for parsers**:

   ```python
   # tests/fuzz/fuzz_pdf_parser.py
   import atheris
   import sys

   with atheris.instrument_imports():
       from src.tools.pdf_parser import PDFParser

   def fuzz_pdf_parser(data):
       """Fuzz the PDF parser with random data."""
       try:
           parser = PDFParser()
           parser.parse_bytes(data)
       except (ValueError, TypeError):
           # Expected exceptions for invalid input
           pass
       except Exception as e:
           # Unexpected exception - potential bug
           raise

   if __name__ == "__main__":
       atheris.Setup(sys.argv, fuzz_pdf_parser)
       atheris.Fuzz()
   ```

3. **Create fuzz tests for URL handling**:

   ```python
   # tests/fuzz/fuzz_url_handler.py
   import atheris
   import sys

   with atheris.instrument_imports():
       from src.tools.browser import BrowserTool

   def fuzz_url_handler(data):
       """Fuzz URL validation and handling."""
       try:
           url = data.decode("utf-8", errors="replace")
           BrowserTool.validate_url(url)
       except (ValueError, UnicodeError):
           pass

   if __name__ == "__main__":
       atheris.Setup(sys.argv, fuzz_url_handler)
       atheris.Fuzz()
   ```

4. **Create fuzz tests for JSON parsing**:

   ```python
   # tests/fuzz/fuzz_json_handler.py
   def fuzz_research_request(data):
       """Fuzz research request parsing."""
       try:
           json_str = data.decode("utf-8", errors="replace")
           ResearchRequest.model_validate_json(json_str)
       except (ValueError, ValidationError):
           pass
   ```

5. **Add to pytest with hypothesis**:

   ```python
   from hypothesis import given, strategies as st, settings

   @settings(max_examples=10000)
   @given(st.binary(max_size=10000))
   def test_pdf_parser_no_crash(data):
       """Verify PDF parser doesn't crash on arbitrary input."""
       try:
           parser.parse_bytes(data)
       except (ValueError, TypeError):
           pass  # Expected
       # Any other exception is a bug
   ```

6. **Run fuzzing with corpus**:

   ```bash
   # Create corpus directory with seed inputs
   mkdir -p corpus/pdf
   cp tests/data/sample.pdf corpus/pdf/

   # Run fuzzer
   python tests/fuzz/fuzz_pdf_parser.py corpus/pdf -max_total_time=300
   ```

## Acceptance Criteria

- [ ] Atheris or equivalent fuzzer installed
- [ ] Fuzz tests for PDF parser
- [ ] Fuzz tests for URL validation
- [ ] Fuzz tests for JSON request parsing
- [ ] Seed corpus created for each target
- [ ] Fuzzing runs for 5+ minutes without crashes

## Continuous Fuzzing

Consider OSS-Fuzz integration for continuous fuzzing:

```yaml
# .clusterfuzzlite/project.yaml
fuzzing_engines:
  - libfuzzer
language: python
main_repo: https://github.com/org/company-researcher
```

## Related Issues

- [TE-003](TE-003-no-security-tests.md) - No security testing
- [TE-020](TE-020-no-property-tests.md) - No property-based testing
