"""Browser Agent for web automation.

This module provides a full browser automation interface for agents to
interact with complex SPAs, fill forms, and navigate web pages.

Inspired by OpenHands/OpenHands browser environment.
"""

import asyncio
import base64
import hashlib
import json
import logging
import re
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class BrowserActionType(str, Enum):
    """Types of browser actions."""

    GOTO = "goto"
    CLICK = "click"
    TYPE = "type"
    FILL = "fill"
    SELECT = "select"
    CHECK = "check"
    UNCHECK = "uncheck"
    SCROLL = "scroll"
    HOVER = "hover"
    PRESS = "press"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    GET_TEXT = "get_text"
    GET_ATTRIBUTE = "get_attribute"
    GET_HTML = "get_html"
    EVALUATE = "evaluate"
    BACK = "back"
    FORWARD = "forward"
    REFRESH = "refresh"
    CLOSE = "close"


class BrowserStatus(str, Enum):
    """Status of browser session."""

    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    CLOSED = "closed"


@dataclass
class BrowserAction:
    """Represents a browser action to execute."""

    action_type: BrowserActionType
    args: Dict[str, Any] = field(default_factory=dict)
    action_id: Optional[str] = None
    timeout_ms: int = 30000

    def __post_init__(self):
        """Generate action ID if not provided."""
        if self.action_id is None:
            content = f"{self.action_type.value}:{json.dumps(self.args, sort_keys=True)}"
            self.action_id = hashlib.md5(content.encode()).hexdigest()[:8]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "args": self.args,
            "timeout_ms": self.timeout_ms,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BrowserAction":
        """Deserialize from dictionary."""
        return cls(
            action_type=BrowserActionType(data["action_type"]),
            args=data.get("args", {}),
            action_id=data.get("action_id"),
            timeout_ms=data.get("timeout_ms", 30000),
        )


@dataclass
class BrowserObservation:
    """Observation after a browser action."""

    action_id: str
    success: bool
    url: str = ""
    title: str = ""

    # Content
    dom_snapshot: Optional[str] = None
    accessibility_tree: Optional[Dict[str, Any]] = None
    screenshot_base64: Optional[str] = None

    # Action result
    result: Any = None
    error: Optional[str] = None

    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "action_id": self.action_id,
            "success": self.success,
            "url": self.url,
            "title": self.title,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "has_screenshot": self.screenshot_base64 is not None,
            "has_dom": self.dom_snapshot is not None,
            "has_accessibility": self.accessibility_tree is not None,
        }


@dataclass
class ElementInfo:
    """Information about a DOM element."""

    selector: str
    tag: str
    text: str = ""
    attributes: Dict[str, str] = field(default_factory=dict)
    bounding_box: Optional[Dict[str, float]] = None
    is_visible: bool = True
    is_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "selector": self.selector,
            "tag": self.tag,
            "text": self.text,
            "attributes": self.attributes,
            "bounding_box": self.bounding_box,
            "is_visible": self.is_visible,
            "is_enabled": self.is_enabled,
        }


@dataclass
class AccessibilityNode:
    """Node in the accessibility tree."""

    role: str
    name: str
    description: str = ""
    value: str = ""
    children: List["AccessibilityNode"] = field(default_factory=list)

    # State
    focused: bool = False
    selected: bool = False
    expanded: Optional[bool] = None
    checked: Optional[bool] = None
    disabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "role": self.role,
            "name": self.name,
            "description": self.description,
            "value": self.value,
            "children": [c.to_dict() for c in self.children],
            "focused": self.focused,
            "selected": self.selected,
            "expanded": self.expanded,
            "checked": self.checked,
            "disabled": self.disabled,
        }

    def to_string(self, indent: int = 0) -> str:
        """Convert to string representation."""
        prefix = "  " * indent
        parts = [f"{prefix}[{self.role}] {self.name}"]

        if self.value:
            parts.append(f" = {self.value}")
        if self.disabled:
            parts.append(" (disabled)")
        if self.focused:
            parts.append(" (focused)")

        result = "".join(parts)

        for child in self.children:
            result += "\n" + child.to_string(indent + 1)

        return result


class BaseBrowserDriver(ABC):
    """Abstract base class for browser drivers."""

    @abstractmethod
    async def start(self) -> None:
        """Start the browser."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the browser."""
        pass

    @abstractmethod
    async def execute(self, action: BrowserAction) -> BrowserObservation:
        """Execute a browser action."""
        pass

    @abstractmethod
    async def get_page_info(self) -> Dict[str, Any]:
        """Get current page information."""
        pass


class MockBrowserDriver(BaseBrowserDriver):
    """Mock browser driver for testing."""

    def __init__(self):
        """Initialize mock driver."""
        self.url = "about:blank"
        self.title = "Mock Browser"
        self.content = "<html><body></body></html>"
        self._running = False

    async def start(self) -> None:
        """Start mock browser."""
        self._running = True

    async def stop(self) -> None:
        """Stop mock browser."""
        self._running = False

    async def execute(self, action: BrowserAction) -> BrowserObservation:
        """Execute mock action."""
        import time
        start_time = time.time()

        obs = BrowserObservation(
            action_id=action.action_id,
            success=True,
            url=self.url,
            title=self.title,
        )

        if action.action_type == BrowserActionType.GOTO:
            self.url = action.args.get("url", self.url)
            self.title = f"Page: {self.url}"
            obs.url = self.url
            obs.title = self.title

        elif action.action_type == BrowserActionType.CLICK:
            obs.result = f"Clicked {action.args.get('selector', 'element')}"

        elif action.action_type in (BrowserActionType.TYPE, BrowserActionType.FILL):
            obs.result = f"Typed '{action.args.get('text', '')}'"

        elif action.action_type == BrowserActionType.GET_TEXT:
            obs.result = "Mock text content"

        elif action.action_type == BrowserActionType.SCREENSHOT:
            obs.screenshot_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        elif action.action_type == BrowserActionType.GET_HTML:
            obs.result = self.content
            obs.dom_snapshot = self.content

        elif action.action_type == BrowserActionType.WAIT:
            await asyncio.sleep(action.args.get("ms", 100) / 1000)

        elif action.action_type == BrowserActionType.EVALUATE:
            obs.result = f"Evaluated: {action.args.get('expression', '')}"

        obs.duration_ms = (time.time() - start_time) * 1000
        return obs

    async def get_page_info(self) -> Dict[str, Any]:
        """Get mock page info."""
        return {
            "url": self.url,
            "title": self.title,
            "viewport": {"width": 1280, "height": 720},
        }


class PlaywrightDriver(BaseBrowserDriver):
    """Browser driver using Playwright."""

    def __init__(
        self,
        headless: bool = True,
        browser_type: str = "chromium",
        viewport: Optional[Dict[str, int]] = None,
    ):
        """Initialize Playwright driver."""
        self.headless = headless
        self.browser_type = browser_type
        self.viewport = viewport or {"width": 1280, "height": 720}

        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    async def start(self) -> None:
        """Start Playwright browser."""
        try:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()

            browser_launcher = getattr(self._playwright, self.browser_type)
            self._browser = await browser_launcher.launch(headless=self.headless)

            self._context = await self._browser.new_context(
                viewport=self.viewport,
            )
            self._page = await self._context.new_page()

        except ImportError:
            logger.warning("Playwright not installed, falling back to mock driver")
            raise

    async def stop(self) -> None:
        """Stop Playwright browser."""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def execute(self, action: BrowserAction) -> BrowserObservation:
        """Execute a Playwright action."""
        import time
        start_time = time.time()

        obs = BrowserObservation(
            action_id=action.action_id,
            success=True,
        )

        try:
            if action.action_type == BrowserActionType.GOTO:
                await self._page.goto(
                    action.args["url"],
                    timeout=action.timeout_ms,
                )

            elif action.action_type == BrowserActionType.CLICK:
                await self._page.click(
                    action.args["selector"],
                    timeout=action.timeout_ms,
                )

            elif action.action_type == BrowserActionType.TYPE:
                await self._page.type(
                    action.args["selector"],
                    action.args["text"],
                    timeout=action.timeout_ms,
                )

            elif action.action_type == BrowserActionType.FILL:
                await self._page.fill(
                    action.args["selector"],
                    action.args["text"],
                    timeout=action.timeout_ms,
                )

            elif action.action_type == BrowserActionType.SELECT:
                await self._page.select_option(
                    action.args["selector"],
                    action.args["value"],
                    timeout=action.timeout_ms,
                )

            elif action.action_type == BrowserActionType.CHECK:
                await self._page.check(
                    action.args["selector"],
                    timeout=action.timeout_ms,
                )

            elif action.action_type == BrowserActionType.UNCHECK:
                await self._page.uncheck(
                    action.args["selector"],
                    timeout=action.timeout_ms,
                )

            elif action.action_type == BrowserActionType.SCROLL:
                x = action.args.get("x", 0)
                y = action.args.get("y", 0)
                await self._page.evaluate(f"window.scrollBy({x}, {y})")

            elif action.action_type == BrowserActionType.HOVER:
                await self._page.hover(
                    action.args["selector"],
                    timeout=action.timeout_ms,
                )

            elif action.action_type == BrowserActionType.PRESS:
                await self._page.press(
                    action.args.get("selector", "body"),
                    action.args["key"],
                    timeout=action.timeout_ms,
                )

            elif action.action_type == BrowserActionType.WAIT:
                if "selector" in action.args:
                    await self._page.wait_for_selector(
                        action.args["selector"],
                        timeout=action.timeout_ms,
                    )
                else:
                    await asyncio.sleep(action.args.get("ms", 1000) / 1000)

            elif action.action_type == BrowserActionType.SCREENSHOT:
                screenshot = await self._page.screenshot(
                    full_page=action.args.get("full_page", False),
                )
                obs.screenshot_base64 = base64.b64encode(screenshot).decode()

            elif action.action_type == BrowserActionType.GET_TEXT:
                element = await self._page.query_selector(action.args["selector"])
                if element:
                    obs.result = await element.text_content()

            elif action.action_type == BrowserActionType.GET_ATTRIBUTE:
                element = await self._page.query_selector(action.args["selector"])
                if element:
                    obs.result = await element.get_attribute(action.args["attribute"])

            elif action.action_type == BrowserActionType.GET_HTML:
                if "selector" in action.args:
                    element = await self._page.query_selector(action.args["selector"])
                    if element:
                        obs.result = await element.inner_html()
                else:
                    obs.result = await self._page.content()
                obs.dom_snapshot = obs.result

            elif action.action_type == BrowserActionType.EVALUATE:
                obs.result = await self._page.evaluate(action.args["expression"])

            elif action.action_type == BrowserActionType.BACK:
                await self._page.go_back(timeout=action.timeout_ms)

            elif action.action_type == BrowserActionType.FORWARD:
                await self._page.go_forward(timeout=action.timeout_ms)

            elif action.action_type == BrowserActionType.REFRESH:
                await self._page.reload(timeout=action.timeout_ms)

            obs.url = self._page.url
            obs.title = await self._page.title()

        except Exception as e:
            obs.success = False
            obs.error = str(e)

        obs.duration_ms = (time.time() - start_time) * 1000
        return obs

    async def get_page_info(self) -> Dict[str, Any]:
        """Get current page information."""
        return {
            "url": self._page.url if self._page else "",
            "title": await self._page.title() if self._page else "",
            "viewport": self.viewport,
        }


class BrowserAgent:
    """High-level browser agent interface."""

    def __init__(
        self,
        driver: Optional[BaseBrowserDriver] = None,
        capture_screenshots: bool = True,
        capture_accessibility: bool = True,
    ):
        """Initialize browser agent."""
        self.driver = driver or MockBrowserDriver()
        self.capture_screenshots = capture_screenshots
        self.capture_accessibility = capture_accessibility

        self._history: List[Tuple[BrowserAction, BrowserObservation]] = []
        self._status = BrowserStatus.IDLE
        self._lock = threading.Lock()

    @property
    def status(self) -> BrowserStatus:
        """Get browser status."""
        return self._status

    async def start(self) -> None:
        """Start the browser."""
        await self.driver.start()
        self._status = BrowserStatus.RUNNING

    async def stop(self) -> None:
        """Stop the browser."""
        await self.driver.stop()
        self._status = BrowserStatus.CLOSED

    async def execute(self, action: BrowserAction) -> BrowserObservation:
        """Execute a browser action."""
        obs = await self.driver.execute(action)

        if self.capture_screenshots and not obs.screenshot_base64:
            try:
                screenshot_action = BrowserAction(
                    action_type=BrowserActionType.SCREENSHOT,
                )
                screenshot_obs = await self.driver.execute(screenshot_action)
                obs.screenshot_base64 = screenshot_obs.screenshot_base64
            except Exception:
                pass

        with self._lock:
            self._history.append((action, obs))

        return obs

    async def goto(self, url: str) -> BrowserObservation:
        """Navigate to a URL."""
        action = BrowserAction(
            action_type=BrowserActionType.GOTO,
            args={"url": url},
        )
        return await self.execute(action)

    async def click(self, selector: str) -> BrowserObservation:
        """Click an element."""
        action = BrowserAction(
            action_type=BrowserActionType.CLICK,
            args={"selector": selector},
        )
        return await self.execute(action)

    async def type(self, selector: str, text: str) -> BrowserObservation:
        """Type text into an element."""
        action = BrowserAction(
            action_type=BrowserActionType.TYPE,
            args={"selector": selector, "text": text},
        )
        return await self.execute(action)

    async def fill(self, selector: str, text: str) -> BrowserObservation:
        """Fill text into an element (clears first)."""
        action = BrowserAction(
            action_type=BrowserActionType.FILL,
            args={"selector": selector, "text": text},
        )
        return await self.execute(action)

    async def select(self, selector: str, value: str) -> BrowserObservation:
        """Select an option in a dropdown."""
        action = BrowserAction(
            action_type=BrowserActionType.SELECT,
            args={"selector": selector, "value": value},
        )
        return await self.execute(action)

    async def scroll(self, x: int = 0, y: int = 0) -> BrowserObservation:
        """Scroll the page."""
        action = BrowserAction(
            action_type=BrowserActionType.SCROLL,
            args={"x": x, "y": y},
        )
        return await self.execute(action)

    async def press(self, key: str, selector: str = "body") -> BrowserObservation:
        """Press a key."""
        action = BrowserAction(
            action_type=BrowserActionType.PRESS,
            args={"selector": selector, "key": key},
        )
        return await self.execute(action)

    async def wait(
        self,
        selector: Optional[str] = None,
        ms: int = 1000,
    ) -> BrowserObservation:
        """Wait for element or time."""
        args = {"ms": ms}
        if selector:
            args["selector"] = selector

        action = BrowserAction(
            action_type=BrowserActionType.WAIT,
            args=args,
        )
        return await self.execute(action)

    async def screenshot(self, full_page: bool = False) -> BrowserObservation:
        """Take a screenshot."""
        action = BrowserAction(
            action_type=BrowserActionType.SCREENSHOT,
            args={"full_page": full_page},
        )
        return await self.execute(action)

    async def get_text(self, selector: str) -> BrowserObservation:
        """Get text content of an element."""
        action = BrowserAction(
            action_type=BrowserActionType.GET_TEXT,
            args={"selector": selector},
        )
        return await self.execute(action)

    async def get_html(self, selector: Optional[str] = None) -> BrowserObservation:
        """Get HTML content."""
        args = {}
        if selector:
            args["selector"] = selector

        action = BrowserAction(
            action_type=BrowserActionType.GET_HTML,
            args=args,
        )
        return await self.execute(action)

    async def evaluate(self, expression: str) -> BrowserObservation:
        """Evaluate JavaScript."""
        action = BrowserAction(
            action_type=BrowserActionType.EVALUATE,
            args={"expression": expression},
        )
        return await self.execute(action)

    async def back(self) -> BrowserObservation:
        """Go back."""
        action = BrowserAction(action_type=BrowserActionType.BACK)
        return await self.execute(action)

    async def forward(self) -> BrowserObservation:
        """Go forward."""
        action = BrowserAction(action_type=BrowserActionType.FORWARD)
        return await self.execute(action)

    async def refresh(self) -> BrowserObservation:
        """Refresh the page."""
        action = BrowserAction(action_type=BrowserActionType.REFRESH)
        return await self.execute(action)

    async def get_page_info(self) -> Dict[str, Any]:
        """Get current page information."""
        return await self.driver.get_page_info()

    def get_history(self) -> List[Tuple[BrowserAction, BrowserObservation]]:
        """Get action history."""
        with self._lock:
            return self._history.copy()

    def clear_history(self) -> None:
        """Clear action history."""
        with self._lock:
            self._history.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about browser actions."""
        with self._lock:
            total = len(self._history)
            successful = sum(1 for _, obs in self._history if obs.success)

            by_type: Dict[str, int] = {}
            for action, _ in self._history:
                key = action.action_type.value
                by_type[key] = by_type.get(key, 0) + 1

            avg_duration = 0.0
            if total > 0:
                avg_duration = sum(obs.duration_ms for _, obs in self._history) / total

            return {
                "total_actions": total,
                "successful": successful,
                "failed": total - successful,
                "success_rate": successful / total if total > 0 else 0,
                "by_type": by_type,
                "avg_duration_ms": avg_duration,
            }


class BrowserAgentManager:
    """Manager for multiple browser agents."""

    def __init__(self):
        """Initialize manager."""
        self.agents: Dict[str, BrowserAgent] = {}
        self._lock = threading.Lock()

    def create_agent(
        self,
        agent_id: str,
        use_playwright: bool = False,
        headless: bool = True,
    ) -> BrowserAgent:
        """Create a new browser agent."""
        if use_playwright:
            try:
                driver = PlaywrightDriver(headless=headless)
            except ImportError:
                driver = MockBrowserDriver()
        else:
            driver = MockBrowserDriver()

        agent = BrowserAgent(driver=driver)

        with self._lock:
            self.agents[agent_id] = agent

        return agent

    def get_agent(self, agent_id: str) -> Optional[BrowserAgent]:
        """Get agent by ID."""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[str]:
        """List all agent IDs."""
        return list(self.agents.keys())

    async def stop_agent(self, agent_id: str) -> bool:
        """Stop and remove an agent."""
        agent = self.agents.get(agent_id)
        if agent is None:
            return False

        await agent.stop()

        with self._lock:
            del self.agents[agent_id]

        return True

    async def stop_all(self) -> None:
        """Stop all agents."""
        for agent in self.agents.values():
            await agent.stop()

        with self._lock:
            self.agents.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about all agents."""
        return {
            "total_agents": len(self.agents),
            "agents": {
                agent_id: agent.get_statistics()
                for agent_id, agent in self.agents.items()
            },
        }


_browser_manager: Optional[BrowserAgentManager] = None
_browser_lock = threading.Lock()


def get_browser_manager() -> BrowserAgentManager:
    """Get singleton browser manager."""
    global _browser_manager

    with _browser_lock:
        if _browser_manager is None:
            _browser_manager = BrowserAgentManager()
        return _browser_manager


def reset_browser_manager() -> None:
    """Reset singleton browser manager."""
    global _browser_manager

    with _browser_lock:
        _browser_manager = None
