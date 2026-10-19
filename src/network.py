"""Classes for the network and planned drone movements."""


class Zone:
    """A named zone with a position and occupancy constraints."""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        kind: str = 'normal',
        color: str = 'none',
        capacity: int = 1
    ) -> None:
        """Store the zone's coordinates, type, color and capacity."""
        self.name = name
        self.x = x
        self.y = y
        self.kind = kind
        self.color = color
        self.capacity = capacity


class Link:
    """An undirected connection shared by both travel directions."""

    def __init__(
        self,
        first: str,
        second: str,
        capacity: int = 1
    ) -> None:
        """Store the endpoints and shared connection capacity."""
        self.first = first
        self.second = second
        self.capacity = capacity

    @property
    def key(self) -> tuple[str, str]:
        """Return the canonical reservation identifier."""
        return (min(self.first, self.second),
                max(self.first, self.second))


class Network:
    """The parsed graph and fleet configuration."""

    def __init__(self) -> None:
        """Initialize an empty network with its own dictionaries."""
        self.drones = 0
        self.start = ''
        self.end = ''
        self.zones: dict[str, Zone] = {}
        self.neighbors: dict[str, list[tuple[str, Link]]] = {}


class Step:
    """One wait or complete movement, including its departure time."""

    def __init__(
        self,
        source: str,
        target: str,
        departure: int,
        arrival: int,
        link: Link | None = None
    ) -> None:
        """Store a movement's endpoints, times and optional connection."""
        self.source = source
        self.target = target
        self.departure = departure
        self.arrival = arrival
        self.link = link
