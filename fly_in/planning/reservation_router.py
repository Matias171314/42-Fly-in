"""Dijkstra routing with per-turn zone and connection reservations."""
from collections import defaultdict
from heapq import heappop, heappush

from fly_in.network import Link, Network, Step


class ReservationRouter:
    """Find routes with Dijkstra, then reserve each route for later drones."""

    def __init__(self, network: Network) -> None:
        """Initialize sparse zone and undirected connection reservations."""
        self.net = network
        self.occupancy: dict[tuple[str, int], int] = defaultdict(int)
        self.traffic: dict[tuple[tuple[str, str], int], int] = defaultdict(int)
        self.last_arrival = 0

    def plan(self) -> list[list[Step]]:
        """Plan the fleet, reserving each route before planning the next."""
        self.occupancy.clear()
        self.traffic.clear()
        self.last_arrival = 0
        self._check_reachable()
        routes: list[list[Step]] = []
        for _ in range(self.net.drones):
            route = self._route()
            self._reserve(route)
            routes.append(route)
        return routes

    def _check_reachable(self) -> None:
        """Reject disconnected endpoints before time-expanded searching."""
        seen = {self.net.start}
        pending = [self.net.start]
        while pending:
            source = pending.pop()
            for target, _ in self.net.neighbors[source]:
                if (target not in seen
                        and self.net.zones[target].kind != 'blocked'):
                    seen.add(target)
                    pending.append(target)
        if self.net.end not in seen:
            raise ValueError('no accessible route from start to end')

    def _space(self, name: str, time: int) -> bool:
        """Check occupancy after all departures at the specified turn."""
        return (name in (self.net.start, self.net.end)
                or self.occupancy.get((name, time), 0)
                < self.net.zones[name].capacity)

    def _route(self) -> list[Step]:
        """Find earliest arrival, preferring priority zones on equal costs."""
        initial = (self.net.start, 0)
        # Dijkstra explores the earliest turn first. The second value breaks
        # equal-arrival ties in favor of priority zones.
        queue = [(0, 0, self.net.start)]
        scores = {initial: 0}
        parents: dict[tuple[str, int], Step] = {}
        # Once previous drones finish, a simple path is always available.
        horizon = self.last_arrival + 2 * len(self.net.zones) + 1
        while queue:
            time, penalty, source = heappop(queue)
            if scores.get((source, time)) != penalty:
                continue
            if source == self.net.end:
                route: list[Step] = []
                state = (source, time)
                while state != initial:
                    step = parents[state]
                    route.append(step)
                    state = (step.source, step.departure)
                return list(reversed(route))
            options: list[tuple[str, Link | None]] = [
                (target, link) for target, link in self.net.neighbors[source]
            ]
            options.append((source, None))
            for target, link in options:
                zone = self.net.zones[target]
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

    def _reserve(self, route: list[Step]) -> None:
        """Reserve zone occupancy and every tick of restricted transit."""
        for step in route:
            self.occupancy[(step.target, step.arrival)] += 1
            if step.link:
                for tick in range(step.departure + 1, step.arrival + 1):
                    self.traffic[(step.link.key, tick)] += 1
        self.last_arrival = max(self.last_arrival, route[-1].arrival)
