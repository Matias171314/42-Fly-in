"""Render one space-separated movement line per simulation turn."""
import time

from fly_in.network import Network, Step
from fly_in.presentation.color_palette import ColorPalette


class MovementRenderer:
    """Print arrivals and restricted transit using the subject format."""

    def __init__(self, network: Network, palette: ColorPalette,
                 delay: float = 0.0) -> None:
        """Configure optional token colors and playback delay."""
        self.net = network
        self.palette = palette
        self.delay = delay

    def run(self, routes: list[list[Step]]) -> None:
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
        # LOAD FOR EVALUATION (disabled; preserve the subject output):
        # from collections import Counter
        # positions = {drone: self.net.start
        #              for drone in range(1, self.net.drones + 1)}
        total = max(turns)
        for turn in range(1, total + 1):
            moves = sorted(turns.get(turn, []))
            # Load extension: apply ALL simultaneous moves before counting.
            # positions.update(moves)
            # loads = Counter(positions.values())
            tokens: list[str] = []
            for drone, target in moves:
                token = f'D{drone}-{target}'
                zone = self.net.zones.get(target)
                # Load extension: add only for zone destinations.
                # if zone is not None:
                #     capacity = ('inf' if target in
                #                 (self.net.start, self.net.end)
                #                 else str(zone.capacity))
                #     token += f' [{loads[target]}/{capacity}]'  # 0/inf, 1/2
                # Transit labels do not occupy a zone slot.
                color = zone.color if zone else 'cyan'
                tokens.append(self.palette.paint(token, color))
            print(' '.join(tokens), flush=True)
            if self.delay and turn < total:
                time.sleep(self.delay)
