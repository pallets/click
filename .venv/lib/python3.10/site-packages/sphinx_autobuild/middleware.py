from __future__ import annotations

from typing import TYPE_CHECKING

from starlette.datastructures import MutableHeaders

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send


def web_socket_script(ws_url: str) -> str:
    # language=HTML
    return f"""
<script>
const ws = new WebSocket("ws://{ws_url}/websocket-reload");
ws.onmessage = () => window.location.reload();
</script>
"""


class JavascriptInjectorMiddleware:
    def __init__(self, app: ASGIApp, ws_url: str) -> None:
        self.app = app
        self.script = web_socket_script(ws_url).encode("utf-8")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        add_script = False
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message) -> None:
            nonlocal add_script
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                if headers.get("Content-Type", "").startswith("text/html"):
                    add_script = True
                    if "Content-Length" in headers:
                        length = int(headers["Content-Length"]) + len(self.script)
                        headers["Content-Length"] = str(length)
            elif message["type"] == "http.response.body":
                request_complete = not message.get("more_body", False)
                if add_script and request_complete:
                    message["body"] += self.script
            await send(message)

        await self.app(scope, receive, send_wrapper)
        return
