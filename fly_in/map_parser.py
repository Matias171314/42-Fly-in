"""Strict, line-aware parser for the subject's map format."""
from pathlib import Path

from fly_in.network import Link, Network, Zone


class MapError(ValueError):
    """Invalid map syntax or network configuration."""


class MapParser:
    """Read maps without accepting ambiguous or unknown metadata."""

    def parse(self, path: Path) -> Network:
        """Load a UTF-8 map and report the line of invalid input."""
        network = Network()
        links: set[tuple[str, str]] = set()
        last_line = 0
        with path.open(encoding='utf-8') as stream:
            for number, raw in enumerate(stream, 1):
                line = raw.split('#', 1)[0].strip()
                if not line:
                    continue
                last_line = number
                try:
                    if any(not char.isprintable() and char != "\t"
                           for char in line):
                        raise MapError("nonprintable character in definition")
                    self._line(network, links, line)
                except ValueError as error:
                    raise MapError(f'line {number}: {error}') from error
        if not network.drones:
            raise MapError('end of file: missing nb_drones')
        if not network.start or not network.end:
            raise MapError('end of file: exactly one start and end required')
        self._validate_route(network, last_line)
        return network

    def _validate_route(self, net: Network, last_line: int) -> None:
        """Reject an end that cannot be reached without blocked zones."""
        seen = {net.start}
        pending = [net.start]
        while pending:
            source = pending.pop()
            for target, _ in net.neighbors[source]:
                if (target not in seen
                        and net.zones[target].kind != 'blocked'):
                    seen.add(target)
                    pending.append(target)
        if net.end not in seen:
            raise MapError(f'end of file (after line {last_line}): '
                           'no accessible route from start to end')

    def _positive(self, value: str) -> int:
        """Validate positive decimal integer metadata."""
        if not value.isascii() or not value.isdecimal() or int(value) < 1:
            raise MapError(f'expected positive integer, got {value!r}')
        return int(value)

    def _coordinate(self, value: str) -> int:
        """Read decimal coordinates with an optional leading plus or minus."""
        digits = value[1:] if value.startswith(('+', '-')) else value
        if not digits.isascii() or not digits.isdecimal():
            raise MapError('coordinates must be integers')
        return int(value)

    def _line(self, net: Network, links: set[tuple[str, str]],
              line: str) -> None:
        """Parse one nonempty definition in its network context."""
        prefix, separator, content = line.partition(':')
        content = content.strip()
        if not net.drones:
            if prefix != 'nb_drones' or not separator:
                raise MapError('first definition must be nb_drones')
            net.drones = self._positive(content)
            return
        if not separator or not prefix or not content:
            raise MapError('malformed definition')
        count = 1 if prefix == 'connection' else 3
        fields = content.split(maxsplit=count)
        body = ' '.join(fields[:count])
        metadata = fields[count] if len(fields) > count else ''
        if metadata:
            if not metadata.startswith('[') or not metadata.endswith(']'):
                raise MapError('malformed metadata block')
            metadata = metadata[1:-1]
            if '[' in metadata or ']' in metadata:
                raise MapError('malformed metadata block')
        tags: dict[str, str] = {}
        for token in (metadata or '').split():
            pair = token.split('=')
            if len(pair) != 2 or not all(pair) or pair[0] in tags:
                raise MapError(f'invalid or repeated metadata: {token}')
            tags[pair[0]] = pair[1]
        if prefix == 'connection':
            self._link(net, links, body.strip(), tags)
            return
        if prefix not in ('hub', 'start_hub', 'end_hub'):
            raise MapError(f'unknown definition: {prefix}')
        if tags.keys() - {'zone', 'color', 'max_drones'}:
            raise MapError('unknown zone metadata')
        fields = body.split()
        if len(fields) != 3 or '-' in fields[0]:
            raise MapError('expected unique name without dashes and x y')
        name, x, y = fields
        if name in net.zones:
            raise MapError(f'duplicate zone: {name}')
        x_coord = self._coordinate(x)
        y_coord = self._coordinate(y)
        kind = tags.get('zone', 'normal')
        if kind not in ('normal', 'priority', 'restricted', 'blocked'):
            raise MapError(f'invalid zone type: {kind}')
        capacity = (self._positive(tags.get('max_drones', '1'))
                    if prefix == 'hub' else 1)
        if prefix != 'hub':
            attr = 'start' if prefix == 'start_hub' else 'end'
            if getattr(net, attr):
                raise MapError(f'duplicate {prefix}')
            if kind == 'blocked':
                raise MapError(f'{prefix} cannot be blocked')
            setattr(net, attr, name)
        net.zones[name] = Zone(name, x_coord, y_coord, kind,
                               tags.get('color', 'none'), capacity)
        net.neighbors[name] = []

    def _link(self, net: Network, links: set[tuple[str, str]],
              body: str, tags: dict[str, str]) -> None:
        """Validate and add an undirected connection."""
        if tags.keys() - {'max_link_capacity'}:
            raise MapError('unknown connection metadata')
        names = body.split('-')
        if (len(names) != 2
                or any(name not in net.zones for name in names)):
            raise MapError('link references an undefined zone')
        first, second = names
        link = Link(first, second,
                    self._positive(tags.get('max_link_capacity', '1')))
        if link.key in links:
            raise MapError('duplicate connection')
        links.add(link.key)
        net.neighbors[first].append((second, link))
        net.neighbors[second].append((first, link))
