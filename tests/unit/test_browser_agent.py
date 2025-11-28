"""Tests for browser agent."""

import pytest
import base64

from src.core.browser_agent import (
    AccessibilityNode,
    BrowserAction,
    BrowserActionType,
    BrowserAgent,
    BrowserAgentManager,
    BrowserObservation,
    BrowserStatus,
    ElementInfo,
    MockBrowserDriver,
    get_browser_manager,
    reset_browser_manager,
)


class TestBrowserAction:
    """Tests for BrowserAction class."""

    def test_create_action(self):
        """Test creating an action."""
        action = BrowserAction(
            action_type=BrowserActionType.CLICK,
            args={"selector": "#button"},
        )

        assert action.action_type == BrowserActionType.CLICK
        assert action.action_id is not None

    def test_to_dict(self):
        """Test serialization."""
        action = BrowserAction(
            action_type=BrowserActionType.GOTO,
            args={"url": "https://example.com"},
            timeout_ms=5000,
        )
        data = action.to_dict()

        assert data["action_type"] == "goto"
        assert data["args"]["url"] == "https://example.com"

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "action_type": "fill",
            "args": {"selector": "input", "text": "hello"},
        }
        action = BrowserAction.from_dict(data)

        assert action.action_type == BrowserActionType.FILL
        assert action.args["text"] == "hello"


class TestBrowserObservation:
    """Tests for BrowserObservation class."""

    def test_create_observation(self):
        """Test creating an observation."""
        obs = BrowserObservation(
            action_id="test_1",
            success=True,
            url="https://example.com",
            title="Example",
        )

        assert obs.success is True
        assert obs.url == "https://example.com"

    def test_to_dict(self):
        """Test serialization."""
        obs = BrowserObservation(
            action_id="test_2",
            success=False,
            error="Element not found",
            duration_ms=150.5,
        )
        data = obs.to_dict()

        assert data["success"] is False
        assert data["error"] == "Element not found"
        assert data["duration_ms"] == 150.5


class TestElementInfo:
    """Tests for ElementInfo class."""

    def test_create_element(self):
        """Test creating element info."""
        element = ElementInfo(
            selector="#main",
            tag="div",
            text="Content",
            attributes={"class": "container"},
        )

        assert element.selector == "#main"
        assert element.tag == "div"

    def test_to_dict(self):
        """Test serialization."""
        element = ElementInfo(
            selector="button",
            tag="button",
            is_enabled=False,
        )
        data = element.to_dict()

        assert data["selector"] == "button"
        assert data["is_enabled"] is False


class TestAccessibilityNode:
    """Tests for AccessibilityNode class."""

    def test_create_node(self):
        """Test creating accessibility node."""
        node = AccessibilityNode(
            role="button",
            name="Submit",
            disabled=False,
        )

        assert node.role == "button"
        assert node.name == "Submit"

    def test_to_dict(self):
        """Test serialization."""
        child = AccessibilityNode(role="text", name="Label")
        node = AccessibilityNode(
            role="region",
            name="Form",
            children=[child],
        )
        data = node.to_dict()

        assert data["role"] == "region"
        assert len(data["children"]) == 1

    def test_to_string(self):
        """Test string representation."""
        child = AccessibilityNode(role="text", name="Hello")
        node = AccessibilityNode(
            role="region",
            name="Main",
            children=[child],
        )

        string = node.to_string()

        assert "[region] Main" in string
        assert "[text] Hello" in string


class TestMockBrowserDriver:
    """Tests for MockBrowserDriver class."""

    def setup_method(self):
        """Create driver."""
        self.driver = MockBrowserDriver()

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping."""
        await self.driver.start()
        assert self.driver._running is True

        await self.driver.stop()
        assert self.driver._running is False

    @pytest.mark.asyncio
    async def test_goto(self):
        """Test navigation."""
        await self.driver.start()

        action = BrowserAction(
            action_type=BrowserActionType.GOTO,
            args={"url": "https://example.com"},
        )
        obs = await self.driver.execute(action)

        assert obs.success is True
        assert obs.url == "https://example.com"

    @pytest.mark.asyncio
    async def test_click(self):
        """Test clicking."""
        await self.driver.start()

        action = BrowserAction(
            action_type=BrowserActionType.CLICK,
            args={"selector": "#button"},
        )
        obs = await self.driver.execute(action)

        assert obs.success is True
        assert "Clicked" in str(obs.result)

    @pytest.mark.asyncio
    async def test_type(self):
        """Test typing."""
        await self.driver.start()

        action = BrowserAction(
            action_type=BrowserActionType.TYPE,
            args={"selector": "input", "text": "hello"},
        )
        obs = await self.driver.execute(action)

        assert obs.success is True
        assert "Typed" in str(obs.result)

    @pytest.mark.asyncio
    async def test_screenshot(self):
        """Test screenshot."""
        await self.driver.start()

        action = BrowserAction(action_type=BrowserActionType.SCREENSHOT)
        obs = await self.driver.execute(action)

        assert obs.success is True
        assert obs.screenshot_base64 is not None

    @pytest.mark.asyncio
    async def test_get_page_info(self):
        """Test getting page info."""
        await self.driver.start()

        info = await self.driver.get_page_info()

        assert "url" in info
        assert "title" in info


class TestBrowserAgent:
    """Tests for BrowserAgent class."""

    def setup_method(self):
        """Create agent."""
        self.agent = BrowserAgent()

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping."""
        await self.agent.start()
        assert self.agent.status == BrowserStatus.RUNNING

        await self.agent.stop()
        assert self.agent.status == BrowserStatus.CLOSED

    @pytest.mark.asyncio
    async def test_goto(self):
        """Test navigation."""
        await self.agent.start()

        obs = await self.agent.goto("https://example.com")

        assert obs.success is True
        assert obs.url == "https://example.com"

    @pytest.mark.asyncio
    async def test_click(self):
        """Test clicking."""
        await self.agent.start()

        obs = await self.agent.click("#button")

        assert obs.success is True

    @pytest.mark.asyncio
    async def test_type(self):
        """Test typing."""
        await self.agent.start()

        obs = await self.agent.type("input", "test text")

        assert obs.success is True

    @pytest.mark.asyncio
    async def test_fill(self):
        """Test filling."""
        await self.agent.start()

        obs = await self.agent.fill("input", "fill text")

        assert obs.success is True

    @pytest.mark.asyncio
    async def test_select(self):
        """Test selecting."""
        await self.agent.start()

        obs = await self.agent.select("select", "option1")

        assert obs.success is True

    @pytest.mark.asyncio
    async def test_scroll(self):
        """Test scrolling."""
        await self.agent.start()

        obs = await self.agent.scroll(0, 100)

        assert obs.success is True

    @pytest.mark.asyncio
    async def test_press(self):
        """Test pressing key."""
        await self.agent.start()

        obs = await self.agent.press("Enter")

        assert obs.success is True

    @pytest.mark.asyncio
    async def test_wait(self):
        """Test waiting."""
        await self.agent.start()

        obs = await self.agent.wait(ms=100)

        assert obs.success is True

    @pytest.mark.asyncio
    async def test_screenshot(self):
        """Test screenshot."""
        await self.agent.start()

        obs = await self.agent.screenshot()

        assert obs.success is True

    @pytest.mark.asyncio
    async def test_get_text(self):
        """Test getting text."""
        await self.agent.start()

        obs = await self.agent.get_text("#content")

        assert obs.success is True

    @pytest.mark.asyncio
    async def test_get_html(self):
        """Test getting HTML."""
        await self.agent.start()

        obs = await self.agent.get_html()

        assert obs.success is True

    @pytest.mark.asyncio
    async def test_evaluate(self):
        """Test JavaScript evaluation."""
        await self.agent.start()

        obs = await self.agent.evaluate("1 + 1")

        assert obs.success is True

    @pytest.mark.asyncio
    async def test_navigation(self):
        """Test back/forward/refresh."""
        await self.agent.start()

        back_obs = await self.agent.back()
        assert back_obs.success is True

        forward_obs = await self.agent.forward()
        assert forward_obs.success is True

        refresh_obs = await self.agent.refresh()
        assert refresh_obs.success is True

    @pytest.mark.asyncio
    async def test_get_page_info(self):
        """Test getting page info."""
        await self.agent.start()

        info = await self.agent.get_page_info()

        assert "url" in info

    @pytest.mark.asyncio
    async def test_history(self):
        """Test action history."""
        await self.agent.start()
        await self.agent.goto("https://example.com")

        history = self.agent.get_history()

        assert len(history) >= 1

    @pytest.mark.asyncio
    async def test_clear_history(self):
        """Test clearing history."""
        await self.agent.start()
        await self.agent.goto("https://example.com")
        self.agent.clear_history()

        assert len(self.agent.get_history()) == 0

    @pytest.mark.asyncio
    async def test_statistics(self):
        """Test statistics."""
        await self.agent.start()
        await self.agent.goto("https://example.com")
        await self.agent.click("#button")

        stats = self.agent.get_statistics()

        assert stats["total_actions"] >= 2
        assert "by_type" in stats


class TestBrowserAgentManager:
    """Tests for BrowserAgentManager class."""

    def setup_method(self):
        """Create manager."""
        self.manager = BrowserAgentManager()

    def test_create_agent(self):
        """Test creating agent."""
        agent = self.manager.create_agent("test_agent")

        assert agent is not None
        assert "test_agent" in self.manager.list_agents()

    def test_get_agent(self):
        """Test getting agent."""
        self.manager.create_agent("my_agent")
        agent = self.manager.get_agent("my_agent")

        assert agent is not None

    def test_list_agents(self):
        """Test listing agents."""
        self.manager.create_agent("agent1")
        self.manager.create_agent("agent2")

        agents = self.manager.list_agents()

        assert len(agents) == 2
        assert "agent1" in agents
        assert "agent2" in agents

    @pytest.mark.asyncio
    async def test_stop_agent(self):
        """Test stopping agent."""
        agent = self.manager.create_agent("to_stop")
        await agent.start()

        success = await self.manager.stop_agent("to_stop")

        assert success is True
        assert "to_stop" not in self.manager.list_agents()

    @pytest.mark.asyncio
    async def test_stop_all(self):
        """Test stopping all agents."""
        agent1 = self.manager.create_agent("a1")
        agent2 = self.manager.create_agent("a2")
        await agent1.start()
        await agent2.start()

        await self.manager.stop_all()

        assert len(self.manager.list_agents()) == 0

    def test_statistics(self):
        """Test statistics."""
        self.manager.create_agent("stat_agent")

        stats = self.manager.get_statistics()

        assert stats["total_agents"] == 1
        assert "stat_agent" in stats["agents"]


class TestGlobalFunctions:
    """Tests for global functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_browser_manager()

    def teardown_method(self):
        """Reset after each test."""
        reset_browser_manager()

    def test_get_browser_manager_singleton(self):
        """Test singleton behavior."""
        m1 = get_browser_manager()
        m2 = get_browser_manager()
        assert m1 is m2

    def test_reset_browser_manager(self):
        """Test resetting singleton."""
        m1 = get_browser_manager()
        reset_browser_manager()
        m2 = get_browser_manager()
        assert m1 is not m2


class TestBrowserActionTypeEnum:
    """Tests for BrowserActionType enum."""

    def test_all_action_types(self):
        """Test all action types."""
        types = [
            BrowserActionType.GOTO,
            BrowserActionType.CLICK,
            BrowserActionType.TYPE,
            BrowserActionType.FILL,
            BrowserActionType.SELECT,
            BrowserActionType.CHECK,
            BrowserActionType.UNCHECK,
            BrowserActionType.SCROLL,
            BrowserActionType.HOVER,
            BrowserActionType.PRESS,
            BrowserActionType.WAIT,
            BrowserActionType.SCREENSHOT,
            BrowserActionType.GET_TEXT,
            BrowserActionType.GET_ATTRIBUTE,
            BrowserActionType.GET_HTML,
            BrowserActionType.EVALUATE,
            BrowserActionType.BACK,
            BrowserActionType.FORWARD,
            BrowserActionType.REFRESH,
            BrowserActionType.CLOSE,
        ]
        assert len(types) == len(BrowserActionType)

    def test_action_type_values(self):
        """Test action type values."""
        assert BrowserActionType.GOTO.value == "goto"
        assert BrowserActionType.CLICK.value == "click"
