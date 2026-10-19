"""Read a Fly-in map and run the drone simulation."""
import argparse
import sys
from pathlib import Path

from src.map_parser import MapParser
from src.planning.reservation_router import ReservationRouter
from src.presentation.color_palette import ColorPalette
from src.presentation.map_menu import MapMenu
from src.presentation.movement_renderer import MovementRenderer


def parse_arguments() -> argparse.Namespace:
    """Define and read the map path and optional terminal colors."""
    parser = argparse.ArgumentParser(
        description='Fly-in drone routing'
    )
    parser.add_argument(
        'map',
        type=Path,
        nargs='?',
        help='map path; leave empty to open the menu'
    )
    parser.add_argument(
        '--visual',
        action='store_true',
        help='enable colored movement tokens'
    )
    # LOAD FOR DEFENSE: uncomment this argument and the marked renderer code.
    # parser.add_argument(
    #     '--load',
    #     action='store_true',
    #     help='show hub occupancy and capacity for each turn'
    # )
    return parser.parse_args()


def main() -> int:
    """Coordinate map selection, planning and movement output."""
    args = parse_arguments()
    palette = ColorPalette(args.visual)

    try:
        path = args.map
        if path is None:
            path = MapMenu(palette).choose()
        if path is None:
            return 0
        network = MapParser().parse(path)
        routes = ReservationRouter(network).plan()
        MovementRenderer(
            network,
            palette,
            # show_load=args.load  # LOAD FOR DEFENSE
        ).run(routes)
    except (OSError, ValueError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('Simulation interrupted.', file=sys.stderr)
        return 130
    return 0


if __name__ == '__main__':
    main()
