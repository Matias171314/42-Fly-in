"""Typed network and movement records."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Zone:
    """A named zone with a position and occupancy constraints."""

    name: str
    x: int
    y: int
    kind: str = 'normal'
    color: str = 'none'
    capacity: int = 1


@dataclass(frozen=True)
class Link:
    """An undirected connection shared by both travel directions."""

    first: str
    second: str
    capacity: int = 1

    @property
    def key(self) -> tuple[str, str]:
        """Return the canonical reservation identifier."""
        return (min(self.first, self.second),
                max(self.first, self.second))


@dataclass
class Network:
    """The parsed graph and fleet configuration."""

    drones: int = 0
    start: str = ''
    end: str = ''
    zones: dict[str, Zone] = field(default_factory=dict)
    neighbors: dict[str, list[tuple[str, Link]]] = field(default_factory=dict)


@dataclass(frozen=True)
class Step:
    """One wait or complete movement, including its departure time."""

    source: str
    target: str
    departure: int
    arrival: int
    link: Link | None = None
