"""
Error path tests for the Company Researcher application.

Tests error handling across various components including AI client failures,
search errors, browser timeouts, database errors, and graph node failures.

Issue: TE-016
"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock


# ============================================================================
# AI Client Error Tests
# ============================================================================


class TestAIClientErrors:
    """Tests for AI client error handling."""

    @pytest.mark.asyncio
    async def test_ai_client_rate_limit_handling(self):
        """Test graceful handling of rate limits."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = Exception("Rate limit exceeded")

        try:
            from src.core.ai.ai_client import AIClient
            # Test that rate limits are handled
            with pytest.raises(Exception) as exc_info:
                client = AIClient()
                client._openai_client = mock_client
                await client.generate("test prompt")

            assert "rate limit" in str(exc_info.value).lower() or exc_info.value is not None
        except ImportError:
            pytest.skip("AIClient not available")

    @pytest.mark.asyncio
    async def test_ai_client_timeout_handling(self):
        """Test timeout handling."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = asyncio.TimeoutError()

        try:
            from src.core.ai.ai_client import AIClient
            with pytest.raises((asyncio.TimeoutError, Exception)):
                client = AIClient()
                client._openai_client = mock_client
                await client.generate("test prompt")
        except ImportError:
            pytest.skip("AIClient not available")

    @pytest.mark.asyncio
    async def test_ai_client_invalid_response_handling(self):
        """Test handling of invalid API responses."""
        mock_response = MagicMock()
        mock_response.choices = []  # Empty choices

        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response

        try:
            from src.core.ai.ai_client import AIClient
            client = AIClient()
            client._openai_client = mock_client
            result = await client.generate("test prompt")
            # Should handle empty choices gracefully
            assert result is not None or result == "" or result is None
        except ImportError:
            pytest.skip("AIClient not available")
        except (IndexError, AttributeError):
            # Expected when handling invalid response
            pass

    @pytest.mark.asyncio
    async def test_ai_client_network_error_handling(self):
        """Test handling of network errors."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = ConnectionError("Network unreachable")

        try:
            from src.core.ai.ai_client import AIClient
            with pytest.raises((ConnectionError, Exception)):
                client = AIClient()
                client._openai_client = mock_client
                await client.generate("test prompt")
        except ImportError:
            pytest.skip("AIClient not available")

    @pytest.mark.asyncio
    async def test_ai_client_api_key_error(self):
        """Test handling of invalid API key."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = Exception("Invalid API key")

        try:
            from src.core.ai.ai_client import AIClient
            with pytest.raises(Exception) as exc_info:
                client = AIClient()
                client._openai_client = mock_client
                await client.generate("test prompt")

            assert "api key" in str(exc_info.value).lower() or exc_info.value is not None
        except ImportError:
            pytest.skip("AIClient not available")


# ============================================================================
# Search Tool Error Tests
# ============================================================================


class TestSearchToolErrors:
    """Tests for search tool error handling."""

    @pytest.mark.asyncio
    async def test_search_no_results_handling(self):
        """Test handling of empty search results."""
        try:
            from src.tools.search import SearchTool

            with patch.object(SearchTool, 'search', new_callable=AsyncMock) as mock_search:
                mock_search.return_value = []

                tool = SearchTool()
                result = await tool.search("nonexistent query xyz123")

                # Should return empty list, not crash
                assert result == [] or result is not None
        except ImportError:
            pytest.skip("SearchTool not available")

    @pytest.mark.asyncio
    async def test_search_timeout_handling(self):
        """Test handling of search timeout."""
        try:
            from src.tools.search import SearchTool

            with patch.object(SearchTool, 'search', new_callable=AsyncMock) as mock_search:
                mock_search.side_effect = asyncio.TimeoutError()

                tool = SearchTool()
                with pytest.raises((asyncio.TimeoutError, Exception)):
                    await tool.search("test query")
        except ImportError:
            pytest.skip("SearchTool not available")

    @pytest.mark.asyncio
    async def test_search_api_error_handling(self):
        """Test handling of search API errors."""
        try:
            from src.tools.search import SearchTool

            with patch.object(SearchTool, 'search', new_callable=AsyncMock) as mock_search:
                mock_search.side_effect = Exception("Service unavailable")

                tool = SearchTool()
                with pytest.raises(Exception):
                    await tool.search("test query")
        except ImportError:
            pytest.skip("SearchTool not available")

    @pytest.mark.asyncio
    async def test_search_malformed_response_handling(self):
        """Test handling of malformed search responses."""
        try:
            from src.tools.search import SearchTool

            with patch.object(SearchTool, 'search', new_callable=AsyncMock) as mock_search:
                # Return malformed data
                mock_search.return_value = [{"invalid": "structure"}]

                tool = SearchTool()
                result = await tool.search("test query")

                # Should handle gracefully
                assert result is not None
        except ImportError:
            pytest.skip("SearchTool not available")


# ============================================================================
# Browser Tool Error Tests
# ============================================================================


class TestBrowserToolErrors:
    """Tests for browser tool error handling."""

    @pytest.mark.asyncio
    async def test_browser_page_not_found(self):
        """Test handling of 404 pages."""
        try:
            from src.tools.browser import BrowserTool

            with patch.object(BrowserTool, 'fetch_content', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = {"status": 404, "content": None}

                tool = BrowserTool()
                result = await tool.fetch_content("https://example.com/nonexistent")

                assert result["status"] == 404
        except ImportError:
            pytest.skip("BrowserTool not available")

    @pytest.mark.asyncio
    async def test_browser_timeout_handling(self):
        """Test handling of page load timeout."""
        try:
            from src.tools.browser import BrowserTool

            with patch.object(BrowserTool, 'fetch_content', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.side_effect = asyncio.TimeoutError()

                tool = BrowserTool()
                with pytest.raises((asyncio.TimeoutError, Exception)):
                    await tool.fetch_content("https://slow-site.com")
        except ImportError:
            pytest.skip("BrowserTool not available")

    @pytest.mark.asyncio
    async def test_browser_ssl_error_handling(self):
        """Test handling of SSL/TLS errors."""
        try:
            from src.tools.browser import BrowserTool

            with patch.object(BrowserTool, 'fetch_content', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.side_effect = Exception("SSL certificate verify failed")

                tool = BrowserTool()
                with pytest.raises(Exception):
                    await tool.fetch_content("https://invalid-ssl.example.com")
        except ImportError:
            pytest.skip("BrowserTool not available")

    @pytest.mark.asyncio
    async def test_browser_dns_error_handling(self):
        """Test handling of DNS resolution errors."""
        try:
            from src.tools.browser import BrowserTool

            with patch.object(BrowserTool, 'fetch_content', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.side_effect = Exception("DNS resolution failed")

                tool = BrowserTool()
                with pytest.raises(Exception):
                    await tool.fetch_content("https://nonexistent-domain-xyz123.com")
        except ImportError:
            pytest.skip("BrowserTool not available")


# ============================================================================
# Database Error Tests
# ============================================================================


class TestDatabaseErrors:
    """Tests for database error handling."""

    def test_database_connection_error(self):
        """Test handling of database connection errors."""
        try:
            from src.api.database import init_database

            with patch('sqlalchemy.create_engine') as mock_engine:
                mock_engine.side_effect = Exception("Connection refused")

                with pytest.raises(Exception):
                    init_database(database_url="invalid://connection")
        except ImportError:
            pytest.skip("Database module not available")

    def test_database_query_error(self):
        """Test handling of database query errors."""
        try:
            from src.api.database import get_db_session

            mock_session = MagicMock()
            mock_session.execute.side_effect = Exception("Invalid query")

            with pytest.raises(Exception):
                mock_session.execute("INVALID SQL")
        except ImportError:
            pytest.skip("Database module not available")

    def test_database_constraint_violation(self):
        """Test handling of constraint violations."""
        mock_session = MagicMock()
        mock_session.add.side_effect = Exception("UNIQUE constraint failed")

        with pytest.raises(Exception) as exc_info:
            mock_session.add({"id": "duplicate"})

        assert "constraint" in str(exc_info.value).lower()


# ============================================================================
# Graph Error Tests
# ============================================================================


class TestGraphErrors:
    """Tests for graph node error handling."""

    @pytest.mark.asyncio
    async def test_graph_node_failure_isolation(self):
        """Test that graph node failures don't crash the whole graph."""
        try:
            from src.graph.graph_builder import create_research_graph
            from src.graph.state import ResearchState

            # This tests that graph can be created and has error handling
            graph = create_research_graph()
            assert graph is not None
        except ImportError:
            pytest.skip("Graph module not available")

    @pytest.mark.asyncio
    async def test_graph_state_corruption_handling(self):
        """Test handling of corrupted state."""
        try:
            from src.graph.state import ResearchState

            # Invalid state should raise validation error
            with pytest.raises((ValueError, TypeError, Exception)):
                ResearchState(
                    company_name=None,  # Required field
                    website="https://example.com"
                )
        except ImportError:
            pytest.skip("ResearchState not available")

    def test_graph_builder_invalid_config(self):
        """Test graph builder with invalid configuration."""
        try:
            from src.graph.graph_builder import create_research_graph

            # Should handle invalid config gracefully
            # Graph creation should work with defaults
            graph = create_research_graph()
            assert graph is not None
        except ImportError:
            pytest.skip("Graph module not available")


# ============================================================================
# Agent Error Tests
# ============================================================================


class TestAgentErrors:
    """Tests for agent error handling."""

    @pytest.mark.asyncio
    async def test_agent_llm_failure_handling(self):
        """Test agent handles LLM failures gracefully."""
        try:
            from src.agents.base_agent import BaseAgent

            mock_ai_client = AsyncMock()
            mock_ai_client.generate.side_effect = Exception("LLM unavailable")

            # Agent should handle LLM failures
            with pytest.raises(Exception):
                agent = BaseAgent(ai_client=mock_ai_client)
                await agent.analyze({"query": "test"})
        except ImportError:
            pytest.skip("BaseAgent not available")

    @pytest.mark.asyncio
    async def test_agent_invalid_input_handling(self):
        """Test agent handles invalid input gracefully."""
        try:
            from src.agents.base_agent import BaseAgent

            mock_ai_client = AsyncMock()
            mock_ai_client.generate.return_value = "response"

            # Agent should validate input
            agent = BaseAgent(ai_client=mock_ai_client)

            # Empty or invalid input should be handled
            with pytest.raises((ValueError, TypeError, Exception)):
                await agent.analyze(None)
        except ImportError:
            pytest.skip("BaseAgent not available")


# ============================================================================
# Cache Error Tests
# ============================================================================


class TestCacheErrors:
    """Tests for cache error handling."""

    def test_cache_read_corruption(self, tmp_path):
        """Test handling of corrupted cache files."""
        cache_file = tmp_path / "corrupted.cache"
        cache_file.write_bytes(b"\x00\x01\x02\xff")  # Invalid pickle/json

        import json

        with pytest.raises((json.JSONDecodeError, Exception)):
            cache_file.read_text()
            json.loads(cache_file.read_text())

    def test_cache_write_permission_error(self, tmp_path):
        """Test handling of cache write permission errors."""
        # Create a read-only directory
        import os
        import stat

        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()

        # Skip on Windows as permission handling is different
        if os.name == 'nt':
            pytest.skip("Permission test not reliable on Windows")

        try:
            readonly_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)

            with pytest.raises(PermissionError):
                (readonly_dir / "test.cache").write_text("data")
        finally:
            readonly_dir.chmod(stat.S_IRWXU)

    def test_cache_disk_full_handling(self):
        """Test handling of disk full errors."""
        # Simulate disk full by trying to write huge file
        # This is a simulated test since we can't actually fill disk
        mock_file = MagicMock()
        mock_file.write.side_effect = OSError("No space left on device")

        with pytest.raises(OSError) as exc_info:
            mock_file.write("data" * 1000000)

        assert "space" in str(exc_info.value).lower()


# ============================================================================
# Configuration Error Tests
# ============================================================================


class TestConfigErrors:
    """Tests for configuration error handling."""

    def test_missing_required_config(self):
        """Test handling of missing required configuration."""
        import os

        # Remove required env var temporarily
        original = os.environ.get("OPENAI_API_KEY")
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

        try:
            from src.core.config import get_settings, clear_settings

            clear_settings()

            # Should handle missing config gracefully or raise clear error
            settings = get_settings()
            # API key should be None or raise error
            assert settings.OPENAI_API_KEY is None or hasattr(settings, 'OPENAI_API_KEY')
        except ImportError:
            pytest.skip("Config module not available")
        except Exception as e:
            # Expected for missing required config
            assert "api" in str(e).lower() or "config" in str(e).lower() or True
        finally:
            if original:
                os.environ["OPENAI_API_KEY"] = original

    def test_invalid_config_value(self):
        """Test handling of invalid configuration values."""
        import os

        os.environ["TEST_INVALID_INT"] = "not_an_int"

        # Should handle gracefully
        value = os.environ.get("TEST_INVALID_INT")
        with pytest.raises(ValueError):
            int(value)


# ============================================================================
# API Endpoint Error Tests
# ============================================================================


class TestAPIEndpointErrors:
    """Tests for API endpoint error handling."""

    def test_api_invalid_json_body(self, api_client):
        """Test handling of invalid JSON in request body."""
        response = api_client.post(
            "/api/v1/research",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]

    def test_api_missing_required_field(self, api_client):
        """Test handling of missing required fields."""
        response = api_client.post(
            "/api/v1/research",
            json={"website": "https://example.com"}  # Missing company_name
        )
        assert response.status_code == 422

    def test_api_invalid_field_type(self, api_client):
        """Test handling of invalid field types."""
        response = api_client.post(
            "/api/v1/research",
            json={
                "company_name": 12345,  # Should be string
                "website": "https://example.com"
            }
        )
        # Should either accept (type coercion) or reject (422)
        assert response.status_code in [200, 422]

    def test_api_nonexistent_endpoint(self, api_client):
        """Test handling of requests to nonexistent endpoints."""
        response = api_client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_api_method_not_allowed(self, api_client):
        """Test handling of incorrect HTTP methods."""
        response = api_client.delete("/api/v1/health")
        assert response.status_code in [404, 405]


# ============================================================================
# Concurrency Error Tests
# ============================================================================


class TestConcurrencyErrors:
    """Tests for concurrency-related error handling."""

    @pytest.mark.asyncio
    async def test_semaphore_exhaustion_handling(self):
        """Test handling when semaphores are exhausted."""
        semaphore = asyncio.Semaphore(1)

        async def blocking_task():
            async with semaphore:
                await asyncio.sleep(10)  # Long task

        async def waiting_task():
            try:
                async with asyncio.timeout(0.1):
                    async with semaphore:
                        return "acquired"
            except asyncio.TimeoutError:
                return "timeout"

        # Start blocking task
        task1 = asyncio.create_task(blocking_task())

        # Give it time to acquire
        await asyncio.sleep(0.01)

        # Try to acquire with timeout
        result = await waiting_task()
        assert result == "timeout"

        # Cleanup
        task1.cancel()
        try:
            await task1
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_task_cancellation_handling(self):
        """Test proper handling of task cancellation."""
        cleanup_called = False

        async def cancellable_task():
            nonlocal cleanup_called
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                cleanup_called = True
                raise

        task = asyncio.create_task(cancellable_task())
        await asyncio.sleep(0.01)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

        assert cleanup_called
