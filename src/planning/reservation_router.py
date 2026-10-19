"""Dijkstra routing with per-turn zone and connection reservations."""
from heapq import heappop, heappush

from src.network import Link, Network, Step


class ReservationRouter:
    """Find routes with Dijkstra, then reserve each route for later drones."""

    def __init__(
        self,
        network: Network
    ) -> None:
        """Initialize sparse zone and undirected connection reservations."""
        self.network = network
        self.occupancy: dict[tuple[str, int], int] = {}
        self.traffic: dict[tuple[tuple[str, str], int], int] = {}
        self.last_arrival = 0

    def plan(self) -> list[list[Step]]:
        """Plan the fleet, reserving each route before planning the next."""
        self.occupancy.clear()
        self.traffic.clear()
        self.last_arrival = 0
        routes: list[list[Step]] = []
        for _ in range(self.network.drones):
            route = self._route()
            self._reserve(route)
            routes.append(route)
        return routes

    def _space(
        self,
        name: str,
        time: int
    ) -> bool:
        """Check occupancy after all departures at the specified turn."""
        return (name in (self.network.start, self.network.end)
                or self.occupancy.get((name, time), 0)
                < self.network.zones[name].capacity)

    def _route(self) -> list[Step]:
        """Find earliest arrival, preferring priority zones on equal costs."""
        initial = (self.network.start, 0)
        queue = [(0, 0, self.network.start)]
        scores = {initial: 0}
        parents: dict[tuple[str, int], Step] = {}
        horizon = self.last_arrival + 2 * len(self.network.zones) + 1
        while queue:
            time, penalty, source = heappop(queue)
            if scores.get((source, time)) != penalty:
                continue
            if source == self.network.end:
                route: list[Step] = []
                state = (source, time)
                while state != initial:
                    step = parents[state]
                    route.append(step)
                    state = (step.source, step.departure)
                return list(reversed(route))
            options: list[tuple[str, Link | None]] = [
                (target, link)
                for target, link in self.network.neighbors[source]
            ]
            options.append((source, None))
            for target, link in options:
                zone = self.network.zones[target]
                if zone.kind == 'blocked':
                    continue
                duration = 2 if link and zone.kind == 'restricted' else 1
                arrival = time + duration
                if arrival > horizon or not self._space(target, arrival):
                    continue
                if link and any(
                    self.traffic.get((link.key, tick), 0) >= link.capacity
                    for tick in range(time + 1, arrival + 1)
                ):
                    continue
                cost = penalty + int(link is not None
                                     and zone.kind != 'priority')
                state = (target, arrival)
                if state in scores and scores[state] <= cost:
                    continue
                scores[state] = cost
                parents[state] = Step(source, target, time, arrival, link)
                heappush(queue, (arrival, cost, target))
        raise ValueError('unable to schedule a route')

    def _reserve(
        self,
        route: list[Step]
    ) -> None:
        """Reserve zone occupancy and every tick of restricted transit."""
        for step in route:
            zone_key = (step.target, step.arrival)
            self.occupancy[zone_key] = self.occupancy.get(zone_key, 0) + 1
            if step.link:
                for tick in range(step.departure + 1, step.arrival + 1):
                    link_key = (step.link.key, tick)
                    self.traffic[link_key] = self.traffic.get(link_key, 0) + 1
        self.last_arrival = max(self.last_arrival, route[-1].arrival)
