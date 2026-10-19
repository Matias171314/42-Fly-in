"""Render one space-separated movement line per simulation turn."""

from src.network import Network, Step
from src.presentation.color_palette import ColorPalette


class MovementRenderer:
    """Print arrivals and restricted transit using the subject format."""

    def __init__(
        self,
        network: Network,
        palette: ColorPalette,
        # show_load: bool = False  # LOAD FOR DEFENSE
    ) -> None:
        """Store the network and movement colors."""
        self.network = network
        self.palette = palette
        # self.show_load = show_load  # LOAD FOR DEFENSE

    def run(
        self,
        routes: list[list[Step]]
    ) -> None:
        """Print only moving drones, with a blank line for idle turns."""
        turns: dict[int, list[tuple[int, str]]] = {}
        for drone, route in enumerate(routes, 1):
            for step in route:
                if step.link is None:
                    continue
                if step.arrival - step.departure == 2:
                    turns.setdefault(step.departure + 1, []).append(
                        (drone, f'{step.source}-{step.target}'))
                turns.setdefault(step.arrival, []).append((drone, step.target))
        # LOAD FOR DEFENSE: initialize each drone's position.
        # positions: dict[int, str] = {}
        # if self.show_load:
        #     for drone in range(1, self.network.drones + 1):
        #         positions[drone] = self.network.start
        total = max(turns)
        for turn in range(1, total + 1):
            moves = sorted(turns.get(turn, []))
            # LOAD FOR DEFENSE: apply all moves, then count hub occupants.
            # loads: dict[str, int] = {}
            # if self.show_load:
            #     for drone, target in moves:
            #         positions[drone] = target
            #     for hub in positions.values():
            #         if hub in self.network.zones:
            #             loads[hub] = loads.get(hub, 0) + 1
            tokens: list[str] = []
            for drone, target in moves:
                token = f'D{drone}-{target}'
                zone = self.network.zones.get(target)
                # LOAD FOR DEFENSE: append the final hub occupancy/capacity.
                # if self.show_load and zone is not None:
                #     capacity = str(zone.capacity)
                #     if target in (self.network.start, self.network.end):
                #         capacity = 'inf'
                #     token += f' [{loads[target]}/{capacity}]'
                color = zone.color if zone else 'cyan'
                tokens.append(self.palette.paint(token, color))
            print(' '.join(tokens), flush=True)
