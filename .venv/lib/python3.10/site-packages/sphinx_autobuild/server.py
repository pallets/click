from __future__ import annotations

import asyncio
from concurrent.futures import ProcessPoolExecutor
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import watchfiles
from starlette.websockets import WebSocket

if TYPE_CHECKING:
    import os
    from collections.abc import Callable, Sequence

    from starlette.types import Receive, Scope, Send

    from sphinx_autobuild.filter import IgnoreFilter


class RebuildServer:
    def __init__(
        self,
        paths: list[os.PathLike[str]],
        ignore_filter: IgnoreFilter,
        change_callback: Callable[[Sequence[Path]], None],
    ) -> None:
        self.paths = [Path(path).resolve(strict=True) for path in paths]
        self.ignore = ignore_filter
        self.change_callback = change_callback
        self.flag = asyncio.Event()
        self.should_exit = asyncio.Event()

    @asynccontextmanager
    async def lifespan(self, _app) -> AbstractAsyncContextManager[None]:
        task = asyncio.create_task(self.main())
        yield
        self.should_exit.set()
        await task
        return

    async def main(self) -> None:
        tasks = (
            asyncio.create_task(self.watch()),
            asyncio.create_task(self.should_exit.wait()),
        )
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        [task.cancel() for task in pending]
        [task.result() for task in done]

    async def watch(self) -> None:
        async for changes in watchfiles.awatch(
            *self.paths,
            watch_filter=lambda _, path: not self.ignore(path),
        ):
            changed_paths = [Path(path).resolve() for (_, path) in changes]
            with ProcessPoolExecutor() as pool:
                fut = pool.submit(self.change_callback, changed_paths=changed_paths)
                await asyncio.wrap_future(fut)
            self.flag.set()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] == "websocket"
        ws = WebSocket(scope, receive, send)
        await ws.accept()

        tasks = (
            asyncio.create_task(self.watch_reloads(ws)),
            asyncio.create_task(self.wait_client_disconnect(ws)),
        )
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        [task.cancel() for task in pending]
        [task.result() for task in done]

    async def watch_reloads(self, ws: WebSocket) -> None:
        while True:
            await self.flag.wait()
            self.flag.clear()
            await ws.send_text("refresh")

    @staticmethod
    async def wait_client_disconnect(ws: WebSocket) -> None:
        async for _ in ws.iter_text():
            pass
