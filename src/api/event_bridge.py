import asyncio
import logging
from typing import Dict, Any

from src.core.logging.events import get_event_stream, Event, EventType
from src.api.websocket import get_connection_manager

logger = logging.getLogger("api.event_bridge")


class EventBridge:
    """
    Bridges system events to the WebSocket manager.
    Subscribes to the global EventStream and broadcasts events to connected dashboard clients.
    """

    def __init__(self):
        self.event_stream = get_event_stream()
        self.connection_manager = get_connection_manager()
        self.subscriber_id = None
        self.is_active = False

    def start(self):
        """Start bridging events."""
        if self.is_active:
            return

        logger.info("Starting EventBridge...")
        self.subscriber_id = self.event_stream.subscribe(
            callback=self._handle_event, is_async=True
        )
        self.is_active = True
        logger.info(f"EventBridge started with subscriber ID: {self.subscriber_id}")

    def stop(self):
        """Stop bridging events."""
        if not self.is_active or not self.subscriber_id:
            return

        logger.info("Stopping EventBridge...")
        self.event_stream.unsubscribe(self.subscriber_id)
        self.subscriber_id = None
        self.is_active = False
        logger.info("EventBridge stopped")

    async def _handle_event(self, event: Event):
        """
        Handle incoming system event.
        Forwards relevant events to WebSocket clients.
        """
        # Filter out internal or noisy events if needed
        # For now, we forward everything to let the frontend decide

        message = {"type": "event", "data": event.to_dict()}

        await self.connection_manager.broadcast(message)


# Global instance
_bridge = None


def get_event_bridge() -> EventBridge:
    global _bridge
    if _bridge is None:
        _bridge = EventBridge()
    return _bridge
