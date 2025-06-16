"""Logic for dealing with sphinx style inventories (e.g. `objects.inv`).

These contain mappings of reference names to ids, scoped by domain and object type.

This is adapted from the Sphinx inventory.py module.
We replicate it here, so that it can be used without Sphinx.
"""

from __future__ import annotations

import argparse
import functools
import json
import re
import zlib
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from typing import IO, TYPE_CHECKING, TypedDict
from urllib.request import urlopen

import yaml

if TYPE_CHECKING:
    # domain_type:object_type -> name -> (project, version, loc, text)
    # the `loc` includes the base url, also null `text` is denoted by "-"
    from sphinx.util.typing import Inventory as SphinxInventoryType


class InventoryItemType(TypedDict):
    """A single inventory item."""

    loc: str
    """The location of the item (relative if base_url not None)."""
    text: str | None
    """Implicit text to show for the item."""


class InventoryType(TypedDict):
    """Inventory data."""

    name: str
    """The name of the project."""
    version: str
    """The version of the project."""
    base_url: str | None
    """The base URL of the `loc`."""
    objects: dict[str, dict[str, dict[str, InventoryItemType]]]
    """Mapping of domain -> object type -> name -> item."""


def from_sphinx(inv: SphinxInventoryType) -> InventoryType:
    """Convert from a Sphinx compliant format."""
    project = ""
    version = ""
    objs: dict[str, dict[str, dict[str, InventoryItemType]]] = {}
    for domain_obj_name, data in inv.items():
        if ":" not in domain_obj_name:
            continue

        domain_name, obj_type = domain_obj_name.split(":", 1)
        objs.setdefault(domain_name, {}).setdefault(obj_type, {})
        for refname, refdata in data.items():
            project, version, uri, text = refdata
            objs[domain_name][obj_type][refname] = {
                "loc": uri,
                "text": None if (not text or text == "-") else text,
            }

    return {
        "name": project,
        "version": version,
        "base_url": None,
        "objects": objs,
    }


def to_sphinx(inv: InventoryType) -> SphinxInventoryType:
    """Convert to a Sphinx compliant format."""
    objs: SphinxInventoryType = {}
    for domain_name, obj_types in inv["objects"].items():
        for obj_type, refs in obj_types.items():
            for refname, refdata in refs.items():
                objs.setdefault(f"{domain_name}:{obj_type}", {})[refname] = (
                    inv["name"],
                    inv["version"],
                    refdata["loc"],
                    refdata["text"] or "-",
                )
    return objs


def load(stream: IO, base_url: str | None = None) -> InventoryType:
    """Load inventory data from a stream."""
    reader = InventoryFileReader(stream)
    line = reader.readline().rstrip()
    if line == "# Sphinx inventory version 1":
        return _load_v1(reader, base_url)
    elif line == "# Sphinx inventory version 2":
        return _load_v2(reader, base_url)
    else:
        raise ValueError(f"invalid inventory header: {line}")


def _load_v1(stream: InventoryFileReader, base_url: str | None) -> InventoryType:
    """Load inventory data (format v1) from a stream."""
    projname = stream.readline().rstrip()[11:]
    version = stream.readline().rstrip()[11:]
    invdata: InventoryType = {
        "name": projname,
        "version": version,
        "base_url": base_url,
        "objects": {},
    }
    for line in stream.readlines():
        name, objtype, location = line.rstrip().split(None, 2)
        # version 1 did not add anchors to the location
        domain = "py"
        if objtype == "mod":
            objtype = "module"
            location += "#module-" + name
        else:
            location += "#" + name
        invdata["objects"].setdefault(domain, {}).setdefault(objtype, {})
        invdata["objects"][domain][objtype][name] = {"loc": location, "text": None}

    return invdata


def _load_v2(stream: InventoryFileReader, base_url: str | None) -> InventoryType:
    """Load inventory data (format v2) from a stream."""
    projname = stream.readline().rstrip()[11:]
    version = stream.readline().rstrip()[11:]
    invdata: InventoryType = {
        "name": projname,
        "version": version,
        "base_url": base_url,
        "objects": {},
    }
    line = stream.readline()
    if "zlib" not in line:
        raise ValueError(f"invalid inventory header (not compressed): {line}")

    for line in stream.read_compressed_lines():
        # be careful to handle names with embedded spaces correctly
        m = re.match(r"(?x)(.+?)\s+(\S+)\s+(-?\d+)\s+?(\S*)\s+(.*)", line.rstrip())
        if not m:
            continue
        name: str
        type: str
        name, type, _, location, text = m.groups()
        if ":" not in type:
            # wrong type value. type should be in the form of "{domain}:{objtype}"
            #
            # Note: To avoid the regex DoS, this is implemented in python (refs: #8175)
            continue
        if (
            type == "py:module"
            and type in invdata["objects"]
            and name in invdata["objects"][type]
        ):
            # due to a bug in 1.1 and below,
            # two inventory entries are created
            # for Python modules, and the first
            # one is correct
            continue
        if location.endswith("$"):
            location = location[:-1] + name
        domain, objtype = type.split(":", 1)
        invdata["objects"].setdefault(domain, {}).setdefault(objtype, {})
        if not text or text == "-":
            text = None
        invdata["objects"][domain][objtype][name] = {"loc": location, "text": text}
    return invdata


_BUFSIZE = 16 * 1024


class InventoryFileReader:
    """A file reader for an inventory file.

    This reader supports mixture of texts and compressed texts.
    """

    def __init__(self, stream: IO) -> None:
        self.stream = stream
        self.buffer = b""
        self.eof = False

    def read_buffer(self) -> None:
        chunk = self.stream.read(_BUFSIZE)
        if chunk == b"":
            self.eof = True
        self.buffer += chunk

    def readline(self) -> str:
        pos = self.buffer.find(b"\n")
        if pos != -1:
            line = self.buffer[:pos].decode()
            self.buffer = self.buffer[pos + 1 :]
        elif self.eof:
            line = self.buffer.decode()
            self.buffer = b""
        else:
            self.read_buffer()
            line = self.readline()

        return line

    def readlines(self) -> Iterator[str]:
        while not self.eof:
            line = self.readline()
            if line:
                yield line

    def read_compressed_chunks(self) -> Iterator[bytes]:
        decompressor = zlib.decompressobj()
        while not self.eof:
            self.read_buffer()
            yield decompressor.decompress(self.buffer)
            self.buffer = b""
        yield decompressor.flush()

    def read_compressed_lines(self) -> Iterator[str]:
        buf = b""
        for chunk in self.read_compressed_chunks():
            buf += chunk
            pos = buf.find(b"\n")
            while pos != -1:
                yield buf[:pos].decode()
                buf = buf[pos + 1 :]
                pos = buf.find(b"\n")


@functools.lru_cache(maxsize=256)
def _create_regex(pat: str) -> re.Pattern[str]:
    r"""Create a regex from a pattern, that can include `*` wildcards,
    to match 0 or more characters.

    `\*` is translated as a literal `*`.
    """
    regex = ""
    backslash_last = False
    for char in pat:
        if backslash_last and char == "*":
            regex += re.escape(char)
            backslash_last = False
            continue
        if backslash_last:
            regex += re.escape("\\")
        backslash_last = False
        if char == "\\":
            backslash_last = True
            continue
        if char == "*":
            regex += ".*"
            continue
        regex += re.escape(char)

    return re.compile(regex)


def match_with_wildcard(name: str, pattern: str | None) -> bool:
    r"""Match a whole name with a pattern, that can include `*` wildcards,
    to match 0 or more characters.

    To include a literal `*` in the pattern, use `\*`.
    """
    if pattern is None:
        return True
    regex = _create_regex(pattern)
    return regex.fullmatch(name) is not None


@dataclass
class InvMatch:
    """A match from an inventory."""

    inv: str
    domain: str
    otype: str
    name: str
    project: str
    version: str
    base_url: str | None
    loc: str
    text: str | None

    def asdict(self) -> dict[str, str]:
        return asdict(self)


def filter_inventories(
    inventories: dict[str, InventoryType],
    *,
    invs: str | None = None,
    domains: str | None = None,
    otypes: str | None = None,
    targets: str | None = None,
) -> Iterator[InvMatch]:
    r"""Filter a set of inventories.

    Filters are strings that can include `*` wildcards, to match 0 or more characters.
     To include a literal `*` in the pattern, use `\*`.

    :param inventories: Mapping of inventory name to inventory data
    :param invs: the inventory key filter
    :param domains: the domain name filter
    :param otypes: the object type filter
    :param targets: the target name filter
    """
    for inv_name, inv_data in inventories.items():
        if not match_with_wildcard(inv_name, invs):
            continue
        for domain_name, dom_data in inv_data["objects"].items():
            if not match_with_wildcard(domain_name, domains):
                continue
            for obj_type, obj_data in dom_data.items():
                if not match_with_wildcard(obj_type, otypes):
                    continue
                for target, item_data in obj_data.items():
                    if match_with_wildcard(target, targets):
                        yield InvMatch(
                            inv=inv_name,
                            domain=domain_name,
                            otype=obj_type,
                            name=target,
                            project=inv_data["name"],
                            version=inv_data["version"],
                            base_url=inv_data["base_url"],
                            loc=item_data["loc"],
                            text=item_data["text"],
                        )


def filter_sphinx_inventories(
    inventories: dict[str, SphinxInventoryType],
    *,
    invs: str | None = None,
    domains: str | None = None,
    otypes: str | None = None,
    targets: str | None = None,
) -> Iterator[InvMatch]:
    r"""Filter a set of sphinx style inventories.

    Filters are strings that can include `*` wildcards, to match 0 or more characters.
     To include a literal `*` in the pattern, use `\*`.

    :param inventories: Mapping of inventory name to inventory data
    :param invs: the inventory key filter
    :param domains: the domain name filter
    :param otypes: the object type filter
    :param targets: the target name filter
    """
    for inv_name, inv_data in inventories.items():
        if not match_with_wildcard(inv_name, invs):
            continue
        for domain_obj_name, data in inv_data.items():
            if ":" not in domain_obj_name:
                continue
            domain_name, obj_type = domain_obj_name.split(":", 1)
            if not (
                match_with_wildcard(domain_name, domains)
                and match_with_wildcard(obj_type, otypes)
            ):
                continue
            for target in data:
                if match_with_wildcard(target, targets):
                    project, version, loc, text = data[target]
                    yield (
                        InvMatch(
                            inv=inv_name,
                            domain=domain_name,
                            otype=obj_type,
                            name=target,
                            project=project,
                            version=version,
                            base_url=None,
                            loc=loc,
                            text=None if (not text or text == "-") else text,
                        )
                    )


def filter_string(
    invs: str | None,
    domains: str | None,
    otype: str | None,
    target: str | None,
    *,
    delimiter: str = ":",
) -> str:
    """Create a string representation of the filter, from the given arguments."""
    str_items = []
    for item in (invs, domains, otype, target):
        if item is None:
            str_items.append("*")
        elif delimiter in item:
            str_items.append(f'"{item}"')
        else:
            str_items.append(f"{item}")
    return delimiter.join(str_items)


def fetch_inventory(
    uri: str, *, timeout: None | float = None, base_url: None | str = None
) -> InventoryType:
    """Fetch an inventory from a URL or local path."""
    if uri.startswith(("http://", "https://")):
        with urlopen(uri, timeout=timeout) as stream:
            return load(stream, base_url=base_url)
    with open(uri, "rb") as stream:
        return load(stream, base_url=base_url)


def inventory_cli(inputs: None | list[str] = None):
    """Command line interface for fetching and parsing an inventory."""
    parser = argparse.ArgumentParser(description="Parse an inventory file.")
    parser.add_argument("uri", metavar="[URL|PATH]", help="URI of the inventory file")
    parser.add_argument(
        "-d",
        "--domain",
        metavar="DOMAIN",
        default="*",
        help="Filter the inventory by domain (`*` = wildcard)",
    )
    parser.add_argument(
        "-o",
        "--object-type",
        metavar="TYPE",
        default="*",
        help="Filter the inventory by object type (`*` = wildcard)",
    )
    parser.add_argument(
        "-n",
        "--name",
        metavar="NAME",
        default="*",
        help="Filter the inventory by reference name (`*` = wildcard)",
    )
    parser.add_argument(
        "-l",
        "--loc",
        metavar="LOC",
        help="Filter the inventory by reference location (`*` = wildcard)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["yaml", "json"],
        default="yaml",
        help="Output format",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        metavar="SECONDS",
        help="Timeout for fetching the inventory",
    )
    args = parser.parse_args(inputs)

    base_url = None
    if args.uri.startswith("http://") or args.uri.startswith("https://"):
        try:
            with urlopen(args.uri, timeout=args.timeout) as stream:
                invdata = load(stream)
            base_url = args.uri.rsplit("/", 1)[0]
        except Exception:
            with urlopen(args.uri + "/objects.inv", timeout=args.timeout) as stream:
                invdata = load(stream)
            base_url = args.uri
    else:
        with open(args.uri, "rb") as stream:
            invdata = load(stream)

    filtered: InventoryType = {
        "name": invdata["name"],
        "version": invdata["version"],
        "base_url": base_url,
        "objects": {},
    }
    for match in filter_inventories(
        {"": invdata},
        domains=args.domain,
        otypes=args.object_type,
        targets=args.name,
    ):
        if args.loc and not match_with_wildcard(match.loc, args.loc):
            continue
        filtered["objects"].setdefault(match.domain, {}).setdefault(match.otype, {})[
            match.name
        ] = {
            "loc": match.loc,
            "text": match.text,
        }

    if args.format == "json":
        print(json.dumps(filtered, indent=2, sort_keys=False))
    else:
        print(yaml.dump(filtered, sort_keys=False))


if __name__ == "__main__":
    inventory_cli()
