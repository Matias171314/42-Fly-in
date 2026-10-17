"""Command-line configuration and application coordination."""
import argparse
import math
import sys
from pathlib import Path

from fly_in.map_parser import MapParser
from fly_in.planning.reservation_router import ReservationRouter
from fly_in.presentation.color_palette import ColorPalette
from fly_in.presentation.map_menu import MapMenu
from fly_in.presentation.movement_renderer import MovementRenderer


class Application:
    """Load a map, plan valid routes and print their movement log."""

    def run(self) -> int:
        """Handle arguments and expected failures without tracebacks."""
        parser = argparse.ArgumentParser(description='Fly-in drone routing')
        parser.add_argument('map', type=Path, nargs='?',
                            help='map path; omitted to open the menu')
        visual = parser.add_mutually_exclusive_group()
        visual.add_argument('--visual', action='store_true',
                            help='enable colored movement tokens')
        visual.add_argument('--no-visual', action='store_true',
                            help='print plain movement tokens')
        parser.add_argument('--color', choices=('auto', 'always', 'never'),
                            default='auto')
        parser.add_argument('--delay', type=float, default=0.0,
                            help='seconds between turns (default: 0)')
        args = parser.parse_args()
        if not math.isfinite(args.delay) or args.delay < 0:
            parser.error('--delay must be a finite nonnegative number')
        colored = (not args.no_visual and args.color != 'never'
                   and (args.visual or args.color == 'always'
                        or sys.stdout.isatty()))
        palette = ColorPalette(colored)
        try:
            path = (args.map if args.map is not None
                    else MapMenu(ColorPalette(sys.stderr.isatty())).choose())
            if path is None:
                return 0
            network = MapParser().parse(path)
            planner = ReservationRouter(network)
            routes = planner.plan()
            MovementRenderer(network, palette, args.delay).run(routes)
        except (OSError, UnicodeError, ValueError) as error:
            print(f'Error: {error}', file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            print('Simulation interrupted.', file=sys.stderr)
            return 130
        return 0
