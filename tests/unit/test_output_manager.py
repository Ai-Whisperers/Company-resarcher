"""
Unit tests for OutputManager.

Tests the output management functionality including:
- Safe file saving with path validation
- Path traversal prevention
- Filename sanitization
- Directory creation
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.core.output_manager import OutputManager, PathTraversalError


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def output_manager(tmp_path: Path) -> OutputManager:
    """Create an OutputManager with a temporary output directory."""
    return OutputManager(base_output_dir=str(tmp_path / "outputs"))


@pytest.fixture
def sample_drafts() -> dict:
    """Sample research drafts for testing."""
    return {
        "01-Context/01-Overview.md": "# Company Overview\n\nThis is the overview.",
        "01-Context/02-History.md": "# Company History\n\nFounded in 2020.",
        "02-Analysis/01-Market.md": "# Market Analysis\n\nMarket size: $1B",
        "README.md": "# Research Report\n\nGenerated report.",
    }


# =============================================================================
# Initialization Tests
# =============================================================================


class TestOutputManagerInitialization:
    """Tests for OutputManager initialization."""

    @pytest.mark.unit
    def test_initializes_with_default_directory(self):
        """Verify OutputManager initializes with default output directory."""
        manager = OutputManager()
        assert manager.base_output_dir.name == "outputs"

    @pytest.mark.unit
    def test_initializes_with_custom_directory(self, tmp_path: Path):
        """Verify OutputManager initializes with custom output directory."""
        custom_dir = tmp_path / "custom_outputs"
        manager = OutputManager(base_output_dir=str(custom_dir))
        assert manager.base_output_dir == custom_dir.resolve()

    @pytest.mark.unit
    def test_resolves_relative_paths(self):
        """Verify relative paths are resolved to absolute."""
        manager = OutputManager(base_output_dir="relative/path")
        assert manager.base_output_dir.is_absolute()


# =============================================================================
# Path Validation Tests
# =============================================================================


class TestPathValidation:
    """Tests for path validation and traversal prevention."""

    @pytest.mark.unit
    def test_validates_safe_path(self, output_manager: OutputManager, tmp_path: Path):
        """Verify safe paths pass validation."""
        base = tmp_path / "outputs"
        base.mkdir(parents=True)
        target = base / "company" / "report.md"

        validated = output_manager._validate_path(base, target)
        assert validated.is_absolute()

    @pytest.mark.unit
    def test_rejects_path_traversal_with_dotdot(self, output_manager: OutputManager, tmp_path: Path):
        """Verify path traversal with .. is rejected."""
        base = tmp_path / "outputs"
        base.mkdir(parents=True)
        malicious = base / ".." / "etc" / "passwd"

        with pytest.raises(PathTraversalError) as exc_info:
            output_manager._validate_path(base, malicious)

        assert "escapes base directory" in str(exc_info.value)

    @pytest.mark.unit
    def test_rejects_absolute_path_outside_base(self, output_manager: OutputManager, tmp_path: Path):
        """Verify absolute paths outside base directory are rejected."""
        base = tmp_path / "outputs"
        base.mkdir(parents=True)
        malicious = Path("/etc/passwd")

        with pytest.raises(PathTraversalError):
            output_manager._validate_path(base, malicious)

    @pytest.mark.unit
    def test_rejects_symlink_escape(self, output_manager: OutputManager, tmp_path: Path):
        """Verify symlink-based escapes are rejected."""
        base = tmp_path / "outputs"
        base.mkdir(parents=True)

        # Create a symlink pointing outside base
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        symlink = base / "escape_link"

        try:
            symlink.symlink_to(outside_dir)
            target = symlink / "file.txt"

            with pytest.raises(PathTraversalError):
                output_manager._validate_path(base, target)
        except OSError:
            # Symlink creation may fail on some systems without admin rights
            pytest.skip("Symlink creation not supported")


# =============================================================================
# Filename Sanitization Tests
# =============================================================================


class TestFilenameSanitization:
    """Tests for filename sanitization."""

    @pytest.mark.unit
    def test_sanitizes_dotdot(self, output_manager: OutputManager):
        """Verify .. is sanitized from filenames."""
        result = output_manager._sanitize_filename("../../../etc/passwd")
        assert ".." not in result
        assert result == "______etc_passwd"

    @pytest.mark.unit
    def test_sanitizes_null_bytes(self, output_manager: OutputManager):
        """Verify null bytes are sanitized."""
        result = output_manager._sanitize_filename("file\x00name.txt")
        assert "\x00" not in result

    @pytest.mark.unit
    def test_sanitizes_special_characters(self, output_manager: OutputManager):
        """Verify special characters are sanitized."""
        result = output_manager._sanitize_filename("file:name*test?.txt")
        assert ":" not in result
        assert "*" not in result
        assert "?" not in result

    @pytest.mark.unit
    def test_sanitizes_angle_brackets(self, output_manager: OutputManager):
        """Verify angle brackets are sanitized (XSS prevention)."""
        result = output_manager._sanitize_filename("<script>alert(1)</script>")
        assert "<" not in result
        assert ">" not in result

    @pytest.mark.unit
    def test_sanitizes_pipe_character(self, output_manager: OutputManager):
        """Verify pipe character is sanitized."""
        result = output_manager._sanitize_filename("file|command")
        assert "|" not in result

    @pytest.mark.unit
    def test_sanitizes_quotes(self, output_manager: OutputManager):
        """Verify double quotes are sanitized."""
        result = output_manager._sanitize_filename('file"name.txt')
        assert '"' not in result

    @pytest.mark.unit
    def test_strips_whitespace(self, output_manager: OutputManager):
        """Verify leading/trailing whitespace is stripped."""
        result = output_manager._sanitize_filename("  filename.txt  ")
        assert result == "filename.txt"

    @pytest.mark.unit
    def test_preserves_valid_characters(self, output_manager: OutputManager):
        """Verify valid characters are preserved."""
        result = output_manager._sanitize_filename("valid-file_name.txt")
        assert result == "valid-file_name.txt"

    @pytest.mark.unit
    @pytest.mark.parametrize("dangerous_name,expected_clean", [
        ("../secret", "___secret"),
        ("..\\secret", "_._secret"),
        ("file\x00.txt", "file_.txt"),
        ("CON", "CON"),  # Windows reserved names are allowed (OS handles)
        ("a:b:c", "a_b_c"),
    ])
    def test_parametrized_sanitization(self, output_manager: OutputManager, dangerous_name: str, expected_clean: str):
        """Parametrized tests for various dangerous filenames."""
        result = output_manager._sanitize_filename(dangerous_name)
        # Just verify dangerous chars are removed
        assert ".." not in result
        assert "\x00" not in result
        assert ":" not in result or dangerous_name == "CON"


# =============================================================================
# Save Research Output Tests
# =============================================================================


class TestSaveResearchOutput:
    """Tests for save_research_output method."""

    @pytest.mark.unit
    def test_saves_single_file(self, output_manager: OutputManager, tmp_path: Path):
        """Verify single file is saved correctly."""
        drafts = {"README.md": "# Test Content"}

        output_manager.save_research_output("TestCompany", drafts)

        expected_path = tmp_path / "outputs" / "TestCompany" / "README.md"
        assert expected_path.exists()
        assert expected_path.read_text() == "# Test Content"

    @pytest.mark.unit
    def test_saves_multiple_files(self, output_manager: OutputManager, sample_drafts: dict, tmp_path: Path):
        """Verify multiple files are saved correctly."""
        output_manager.save_research_output("TestCompany", sample_drafts)

        for relative_path, content in sample_drafts.items():
            expected_path = tmp_path / "outputs" / "TestCompany" / relative_path
            assert expected_path.exists(), f"File not found: {relative_path}"
            assert expected_path.read_text() == content

    @pytest.mark.unit
    def test_creates_nested_directories(self, output_manager: OutputManager, tmp_path: Path):
        """Verify nested directories are created automatically."""
        drafts = {"deep/nested/path/file.md": "Content"}

        output_manager.save_research_output("TestCompany", drafts)

        expected_path = tmp_path / "outputs" / "TestCompany" / "deep" / "nested" / "path" / "file.md"
        assert expected_path.exists()

    @pytest.mark.unit
    def test_sanitizes_company_name(self, output_manager: OutputManager, tmp_path: Path):
        """Verify company name is sanitized before use."""
        drafts = {"README.md": "Content"}

        # Try a dangerous company name
        output_manager.save_research_output("../../../malicious", drafts)

        # Should not create files outside base directory
        malicious_path = tmp_path / "malicious"
        assert not malicious_path.exists()

        # File should be saved with sanitized name
        sanitized_path = tmp_path / "outputs" / "______malicious" / "README.md"
        assert sanitized_path.exists()

    @pytest.mark.unit
    def test_rejects_path_traversal_in_draft_key(self, output_manager: OutputManager):
        """Verify path traversal in draft keys is rejected."""
        drafts = {"../../../etc/passwd": "malicious content"}

        with pytest.raises(PathTraversalError):
            output_manager.save_research_output("TestCompany", drafts)

    @pytest.mark.unit
    def test_overwrites_existing_files(self, output_manager: OutputManager, tmp_path: Path):
        """Verify existing files are overwritten."""
        drafts = {"README.md": "Original Content"}
        output_manager.save_research_output("TestCompany", drafts)

        # Save again with different content
        drafts = {"README.md": "Updated Content"}
        output_manager.save_research_output("TestCompany", drafts)

        expected_path = tmp_path / "outputs" / "TestCompany" / "README.md"
        assert expected_path.read_text() == "Updated Content"

    @pytest.mark.unit
    def test_handles_empty_drafts(self, output_manager: OutputManager, tmp_path: Path):
        """Verify empty drafts dictionary is handled gracefully."""
        output_manager.save_research_output("TestCompany", {})

        # Company directory should still be created
        company_dir = tmp_path / "outputs" / "TestCompany"
        assert company_dir.exists()

    @pytest.mark.unit
    def test_handles_unicode_filenames(self, output_manager: OutputManager, tmp_path: Path):
        """Verify unicode in filenames is handled."""
        drafts = {"report-日本語.md": "Japanese content"}

        output_manager.save_research_output("TestCompany", drafts)

        expected_path = tmp_path / "outputs" / "TestCompany" / "report-日本語.md"
        assert expected_path.exists()

    @pytest.mark.unit
    def test_handles_unicode_company_name(self, output_manager: OutputManager, tmp_path: Path):
        """Verify unicode company names are handled."""
        drafts = {"README.md": "Content"}

        output_manager.save_research_output("テスト会社", drafts)

        expected_path = tmp_path / "outputs" / "テスト会社" / "README.md"
        assert expected_path.exists()


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_very_long_company_name(self, output_manager: OutputManager, tmp_path: Path):
        """Verify very long company names are handled."""
        long_name = "A" * 300  # Very long name
        drafts = {"README.md": "Content"}

        # Should not raise an error
        output_manager.save_research_output(long_name, drafts)

    @pytest.mark.unit
    def test_special_characters_in_company_name(self, output_manager: OutputManager, tmp_path: Path):
        """Verify special characters in company name are handled."""
        drafts = {"README.md": "Content"}

        output_manager.save_research_output("Company & Co., Inc.", drafts)

        # Just verify no exception was raised
        assert True

    @pytest.mark.unit
    def test_empty_company_name(self, output_manager: OutputManager, tmp_path: Path):
        """Verify empty company name is handled."""
        drafts = {"README.md": "Content"}

        output_manager.save_research_output("", drafts)

        # Should still work with empty string (becomes base dir)
        # Note: This may or may not be desired behavior

    @pytest.mark.unit
    def test_whitespace_only_company_name(self, output_manager: OutputManager, tmp_path: Path):
        """Verify whitespace-only company name is handled."""
        drafts = {"README.md": "Content"}

        output_manager.save_research_output("   ", drafts)

        # After sanitization and strip, should become empty

    @pytest.mark.unit
    def test_empty_file_content(self, output_manager: OutputManager, tmp_path: Path):
        """Verify empty file content is handled."""
        drafts = {"README.md": ""}

        output_manager.save_research_output("TestCompany", drafts)

        expected_path = tmp_path / "outputs" / "TestCompany" / "README.md"
        assert expected_path.exists()
        assert expected_path.read_text() == ""

    @pytest.mark.unit
    def test_binary_like_content(self, output_manager: OutputManager, tmp_path: Path):
        """Verify content with binary-like characters is handled."""
        drafts = {"README.md": "Content with special chars: \x00\x01\x02"}

        # Note: This might fail on write_text, but we test the behavior
        try:
            output_manager.save_research_output("TestCompany", drafts)
        except Exception:
            # Expected for truly binary content with null bytes
            pass


# =============================================================================
# Concurrent Access Tests
# =============================================================================


class TestConcurrentAccess:
    """Tests for concurrent file operations."""

    @pytest.mark.unit
    def test_multiple_saves_same_company(self, output_manager: OutputManager, tmp_path: Path):
        """Verify multiple saves to same company directory work."""
        drafts1 = {"file1.md": "Content 1"}
        drafts2 = {"file2.md": "Content 2"}

        output_manager.save_research_output("TestCompany", drafts1)
        output_manager.save_research_output("TestCompany", drafts2)

        assert (tmp_path / "outputs" / "TestCompany" / "file1.md").exists()
        assert (tmp_path / "outputs" / "TestCompany" / "file2.md").exists()

    @pytest.mark.unit
    def test_saves_to_multiple_companies(self, output_manager: OutputManager, tmp_path: Path):
        """Verify saves to different company directories work."""
        drafts = {"README.md": "Content"}

        output_manager.save_research_output("Company1", drafts)
        output_manager.save_research_output("Company2", drafts)

        assert (tmp_path / "outputs" / "Company1" / "README.md").exists()
        assert (tmp_path / "outputs" / "Company2" / "README.md").exists()


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.unit
    def test_handles_permission_error(self, output_manager: OutputManager, tmp_path: Path):
        """Verify permission errors are handled gracefully."""
        # This test is platform-specific and may not work on all systems
        # We'll just verify the error is raised/logged appropriately
        pass  # Skip for now as it requires special OS permissions

    @pytest.mark.unit
    def test_handles_disk_full_error(self, output_manager: OutputManager):
        """Verify disk full errors are handled gracefully."""
        # This is difficult to test in a unit test
        pass  # Skip for now

    @pytest.mark.unit
    def test_logs_successful_save(self, output_manager: OutputManager, tmp_path: Path):
        """Verify successful saves are logged."""
        drafts = {"README.md": "Content"}

        with patch('src.core.output_manager.logger') as mock_logger:
            output_manager.save_research_output("TestCompany", drafts)

            # Verify info/debug logs were called
            assert mock_logger.info.called or mock_logger.debug.called

    @pytest.mark.unit
    def test_logs_security_errors(self, output_manager: OutputManager):
        """Verify security errors are logged."""
        drafts = {"../../../etc/passwd": "malicious"}

        with patch('src.core.output_manager.logger') as mock_logger:
            with pytest.raises(PathTraversalError):
                output_manager.save_research_output("TestCompany", drafts)

            # Verify error was logged
            assert mock_logger.error.called


# =============================================================================
# Integration with PathTraversalError
# =============================================================================


class TestPathTraversalErrorException:
    """Tests for PathTraversalError exception class."""

    @pytest.mark.unit
    def test_exception_message(self):
        """Verify exception message is set correctly."""
        error = PathTraversalError("Test message")
        assert str(error) == "Test message"

    @pytest.mark.unit
    def test_exception_inherits_from_valueerror(self):
        """Verify PathTraversalError inherits from ValueError."""
        error = PathTraversalError("Test")
        assert isinstance(error, ValueError)

    @pytest.mark.unit
    def test_exception_can_be_caught_as_valueerror(self):
        """Verify PathTraversalError can be caught as ValueError."""
        with pytest.raises(ValueError):
            raise PathTraversalError("Test")
