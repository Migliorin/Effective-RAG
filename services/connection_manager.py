class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, object] = {}

    async def connect(self, connection_id: str, websocket: object):
        self.active_connections[connection_id] = websocket

    def disconnect(self, connection_id: str):
        self.active_connections.pop(connection_id, None)

    async def send_personal_message(self, message: str, websocket: object):
        await self._send_message(websocket, message)

    async def send_to_connection(self, connection_id: str, message: str):
        websocket = self.active_connections.get(connection_id)
        if websocket is None:
            return

        await self._send_message(websocket, message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await self._send_message(connection, message)

    async def _send_message(self, websocket: object, message: str):
        send_text = getattr(websocket, "send_text", None)
        if callable(send_text):
            await send_text(message)
            return

        send = getattr(websocket, "send", None)
        if callable(send):
            await send(message)
