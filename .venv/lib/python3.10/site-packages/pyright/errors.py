from pathlib import Path

from .types import Target


class PyrightError(Exception):
    message: str

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NodeError(PyrightError):
    pass


class BinaryNotFound(NodeError):
    def __init__(self, target: Target, path: Path) -> None:
        super().__init__(f'Expected {target} binary to exist at {path} but was not found.')
        self.path = path
        self.target = target


class VersionCheckFailed(NodeError):
    pass
