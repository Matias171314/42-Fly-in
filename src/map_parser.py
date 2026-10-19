"""Read map files and validate their zones, connections and metadata."""
from pathlib import Path

from src.network import Link, Network, Zone


class MapError(ValueError):
    """Report an invalid map definition."""


class MapParser:
    """Build a valid network from a map file."""

    def parse(
        self,
        path: Path
    ) -> Network:
        """Read the file, validate every definition and return its network."""
        network = Network()
        connections: set[tuple[str, str]] = set()
        last_line = 0

        with path.open() as map_file:
            for line_number, raw_line in enumerate(map_file, 1):
                line = raw_line.split('#', 1)[0]
                line = line.strip()
                if not line:
                    continue

                last_line = line_number
                try:
                    for character in line:
                        if character < ' ' and character != '\t':
                            raise MapError('invalid control character')
                    self._parse_line(network, connections, line)
                except ValueError as error:
                    raise MapError(f'line {line_number}: {error}') from error

        if network.drones == 0:
            raise MapError('end of file: missing nb_drones')
        if not network.start:
            raise MapError('end of file: missing start_hub')
        if not network.end:
            raise MapError('end of file: missing end_hub')

        self._validate_route(network, last_line)
        return network

    def _parse_line(
        self,
        network: Network,
        connections: set[tuple[str, str]],
        line: str
    ) -> None:
        """Identify the definition and send it to the appropriate method."""
        prefix, separator, content = line.partition(':')
        content = content.strip()

        if network.drones == 0:
            if prefix != 'nb_drones' or not separator:
                raise MapError('first definition must be nb_drones')
            network.drones = self._positive_integer(content)
            return

        if not separator or not content:
            raise MapError('expected a definition, colon and values')
        if prefix not in ('hub', 'start_hub', 'end_hub', 'connection'):
            raise MapError(f'unknown definition: {prefix}')

        field_count = 3
        if prefix == 'connection':
            field_count = 1
        fields = content.split(maxsplit=field_count)

        metadata = ''
        if len(fields) > field_count:
            metadata = fields.pop()
        tags = self._parse_metadata(metadata)

        if prefix == 'connection':
            self._parse_connection(network, connections, fields[0], tags)
        else:
            self._parse_zone(network, prefix, fields, tags)

    def _parse_metadata(
        self,
        text: str
    ) -> dict[str, str]:
        """Convert optional bracketed key=value pairs into a dictionary."""
        tags: dict[str, str] = {}
        if not text:
            return tags

        if not text.startswith('[') or not text.endswith(']'):
            raise MapError('malformed metadata block')
        text = text[1:-1]
        if '[' in text or ']' in text:
            raise MapError('malformed metadata block')

        for token in text.split():
            pair = token.split('=')
            if len(pair) != 2:
                raise MapError(f'expected key=value, got {token!r}')
            key, value = pair
            if not key or not value:
                raise MapError(f'empty metadata key or value: {token}')
            if key in tags:
                raise MapError(f'repeated metadata: {key}')
            tags[key] = value
        return tags

    def _parse_zone(
        self,
        network: Network,
        prefix: str,
        fields: list[str],
        tags: dict[str, str]
    ) -> None:
        """Validate and store a regular, start or end hub."""
        for key in tags:
            if key not in ('zone', 'color', 'max_drones'):
                raise MapError(f'unknown zone metadata: {key}')
        if len(fields) != 3:
            raise MapError('expected a zone name and two coordinates')

        name, x, y = fields
        if '-' in name:
            raise MapError('zone names cannot contain dashes')
        if name in network.zones:
            raise MapError(f'duplicate zone: {name}')
        x_coordinate = self._coordinate(x)
        y_coordinate = self._coordinate(y)

        kind = tags.get('zone', 'normal')
        if kind not in ('normal', 'priority', 'restricted', 'blocked'):
            raise MapError(f'invalid zone type: {kind}')
        capacity = 1
        if prefix == 'hub':
            capacity = self._positive_integer(tags.get('max_drones', '1'))
        else:
            if kind == 'blocked':
                raise MapError(f'{prefix} cannot be blocked')
            if prefix == 'start_hub':
                if network.start:
                    raise MapError('duplicate start_hub')
                network.start = name
            if prefix == 'end_hub':
                if network.end:
                    raise MapError('duplicate end_hub')
                network.end = name

        network.zones[name] = Zone(
            name=name,
            x=x_coordinate,
            y=y_coordinate,
            kind=kind,
            color=tags.get('color', 'none'),
            capacity=capacity
        )
        network.neighbors[name] = []

    def _parse_connection(
        self,
        network: Network,
        connections: set[tuple[str, str]],
        text: str,
        tags: dict[str, str]
    ) -> None:
        """Validate and store a connection in both directions."""
        for key in tags:
            if key != 'max_link_capacity':
                raise MapError(f'unknown connection metadata: {key}')
        names = text.split('-')
        if len(names) != 2:
            raise MapError('expected two zone names separated by a dash')
        first, second = names
        if first not in network.zones or second not in network.zones:
            raise MapError('connection references an undefined zone')

        capacity = self._positive_integer(tags.get('max_link_capacity', '1'))
        link = Link(first, second, capacity)
        if link.key in connections:
            raise MapError('duplicate connection')
        connections.add(link.key)
        network.neighbors[first].append((second, link))
        network.neighbors[second].append((first, link))

    def _positive_integer(
        self,
        value: str
    ) -> int:
        """Require decimal digits and a number greater than zero."""
        if not value:
            raise MapError('expected a positive integer')
        for character in value:
            if character not in '0123456789':
                raise MapError(f'expected positive integer, got {value!r}')
        number = int(value)
        if number < 1:
            raise MapError(f'expected positive integer, got {value!r}')
        return number

    def _coordinate(
        self,
        value: str
    ) -> int:
        """Read integer coordinates with an optional sign."""
        digits = value
        if value.startswith('+') or value.startswith('-'):
            digits = value[1:]
        if not digits:
            raise MapError('coordinates must be integers')
        for character in digits:
            if character not in '0123456789':
                raise MapError('coordinates must be integers')
        return int(value)

    def _validate_route(
        self,
        network: Network,
        last_line: int
    ) -> None:
        """Check that the goal can be reached without blocked zones."""
        visited = {network.start}
        pending = [network.start]
        while pending:
            current = pending.pop()
            for neighbor, _ in network.neighbors[current]:
                if network.zones[neighbor].kind == 'blocked':
                    continue
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                pending.append(neighbor)
        if network.end not in visited:
            raise MapError(f'end of file (after line {last_line}): '
                           'no accessible route from start to end')
