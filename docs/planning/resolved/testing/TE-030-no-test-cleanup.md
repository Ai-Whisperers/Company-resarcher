# TE-030: No Test Cleanup Procedures

**Priority**: Low
**Category**: Testing
**Status**: Completed
**Estimated Effort**: Small
**Completed**: 2025-11-28
**Resolution**: Added session_cleanup autouse fixture for session-level cleanup. Created db_transaction, browser_context, temp_file_tracker, and verify_no_file_leaks fixtures in conftest.py for comprehensive cleanup.

## Description

Tests create files, database entries, and other artifacts but don't consistently clean up. This can cause test pollution and disk space issues.

## Current State

- Some tests leave files behind
- Temp directories not always cleaned
- Database test data may persist
- Mock patches may leak between tests

## Impact

- **Test pollution**: Previous test affects next
- **Disk space**: Accumulated test artifacts
- **Flaky tests**: State from previous runs
- **Debug difficulty**: Unclear what's test artifact

## Artifacts to Clean

| Artifact | Location | Cleanup Method |
|----------|----------|----------------|
| Output files | `data/`, `outputs/` | Delete after test |
| Temp files | System temp | Use `tmp_path` fixture |
| Database entries | SQLite/Postgres | Transaction rollback |
| Browser instances | Memory | Context manager |
| Cache entries | `~/.cache/` | Clear on setup |

## Proposed Solution

1. **Use pytest's tmp_path fixture**:

   ```python
   def test_file_output(tmp_path):
       """Test file generation with automatic cleanup."""
       output_file = tmp_path / "report.md"
       generate_report(output_file)
       assert output_file.exists()
       # tmp_path automatically cleaned after test
   ```

2. **Create cleanup fixtures**:

   ```python
   @pytest.fixture(autouse=True)
   def cleanup_outputs():
       """Clean up output directory before and after tests."""
       output_dir = Path("data/test_outputs")

       # Cleanup before
       if output_dir.exists():
           shutil.rmtree(output_dir)

       yield

       # Cleanup after
       if output_dir.exists():
           shutil.rmtree(output_dir)

   @pytest.fixture
   def db_transaction(db_session):
       """Wrap test in transaction that rolls back."""
       db_session.begin_nested()
       yield db_session
       db_session.rollback()
   ```

3. **Use context managers for resources**:

   ```python
   @pytest.fixture
   async def browser_context():
       """Provide browser that closes after test."""
       async with async_playwright() as p:
           browser = await p.chromium.launch()
           context = await browser.new_context()
           yield context
           await context.close()
           await browser.close()
   ```

4. **Add finalizers for complex cleanup**:

   ```python
   @pytest.fixture
   def temp_cache(request):
       """Create temporary cache that's cleaned up."""
       cache = Cache(path="/tmp/test_cache")

       def cleanup():
           cache.clear()
           shutil.rmtree("/tmp/test_cache", ignore_errors=True)

       request.addfinalizer(cleanup)
       return cache
   ```

5. **Session-level cleanup**:

   ```python
   @pytest.fixture(scope="session", autouse=True)
   def session_cleanup():
       """Clean up at start and end of test session."""
       # Setup: clean slate
       cleanup_test_artifacts()

       yield

       # Teardown: final cleanup
       cleanup_test_artifacts()

   def cleanup_test_artifacts():
       """Remove all test artifacts."""
       paths_to_clean = [
           Path("data/test_*"),
           Path("outputs/test_*"),
           Path(".pytest_cache"),
       ]
       for pattern in paths_to_clean:
           for path in Path.cwd().glob(str(pattern)):
               if path.is_dir():
                   shutil.rmtree(path)
               else:
                   path.unlink()
   ```

6. **Add cleanup verification**:

   ```python
   @pytest.fixture(autouse=True)
   def verify_cleanup():
       """Verify no test pollution after each test."""
       yield

       # Check for leaked files
       test_files = list(Path("data").glob("test_*"))
       assert not test_files, f"Test files not cleaned: {test_files}"
   ```

## Acceptance Criteria

- [ ] All tests use tmp_path for file operations
- [ ] Database tests use transaction rollback
- [ ] Browser/network resources use context managers
- [ ] Session cleanup removes all artifacts
- [ ] Cleanup verification catches leaks
- [ ] No test pollution between runs

## Related Issues

- [TE-032](TE-032-no-test-isolation.md) - Tests not properly isolated
- [TE-029](TE-029-no-parallel-tests.md) - Tests don't run in parallel
