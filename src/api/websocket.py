import asyncio
import json
import logging
from typing import Dict, List, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("api.websocket")


class ConnectionManager:
    """
    Manages WebSocket connections for the live dashboard.
    """

    def __init__(self):
        # List of active connections
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(
            f"Client connected. Total connections: {len(self.active_connections)}"
        )

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(
            f"Client disconnected. Total connections: {len(self.active_connections)}"
        )

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected clients.

        Args:
            message: Dictionary to send as JSON
        """
        if not self.active_connections:
            return

        # Serialize once
        try:
            json_message = json.dumps(message, default=str)
        except Exception as e:
            logger.error(f"Failed to serialize message: {e}")
            return

        # Send to all clients
        async with self._lock:
            # Create a copy to avoid modification during iteration if disconnect happens
            connections = list(self.active_connections)

        for connection in connections:
            try:
                await connection.send_text(json_message)
            except WebSocketDisconnect:
                await self.disconnect(connection)
            except Exception as e:
                logger.warning(f"Error sending to client: {e}")
                await self.disconnect(connection)


# Global instance
manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    return manager
