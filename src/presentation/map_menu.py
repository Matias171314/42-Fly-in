"""Choose a supplied map or enter a custom map path."""
import sys
from pathlib import Path

from src.presentation.color_palette import ColorPalette


class MapMenu:
    """Display the available maps and return the user's selection."""

    def __init__(
        self,
        palette: ColorPalette
    ) -> None:
        """Associate each menu number with its map path."""
        self.palette = palette
        self.maps: dict[str, Path] = {}
        root = Path(__file__).resolve().parents[2] / 'maps'

        for level in ('easy', 'medium', 'hard', 'challenger'):
            for path in sorted((root / level).glob('*.txt')):
                number = str(len(self.maps) + 1)
                self.maps[number] = path

    def choose(self) -> Path | None:
        """Read choices until the user selects a map or quits."""
        self._show()
        while True:
            choice = self._read('\n  Select map: ')
            if choice is None:
                return None
            if choice.lower() == 'q':
                return None
            if choice in self.maps:
                return self.maps[choice]
            if choice.lower() == 'p':
                custom = self._read('  Map path: ')
                if custom is None:
                    return None
                if custom:
                    return Path(custom).expanduser()
            print('  Invalid choice. Enter a map number, p or q.',
                  file=sys.stderr)

    def _show(self) -> None:
        """Print the title, map numbers and other available choices."""
        title = (
            '\n  +--------------------------------------------+\n'
            '  |                F L Y - I N                 |\n'
            '  |          DRONE ROUTING SIMULATOR           |\n'
            '  +--------------------------------------------+\n'
            '  MAP SELECTION'
        )
        print(self.palette.paint(title, 'cyan'), file=sys.stderr)
        previous = ''
        for number, path in self.maps.items():
            level = path.parent.name
            if level != previous:
                print(f'\n  {level.upper()}', file=sys.stderr)
                previous = level
            name = path.stem.replace('_', ' ')
            print(f'  {number:>2}. {name}', file=sys.stderr)
        print('\n  p. Custom map path\n  q. Quit', file=sys.stderr)

    def _read(
        self,
        prompt: str
    ) -> str | None:
        """Read a line; return None when the input is closed."""
        print(prompt, end='', file=sys.stderr, flush=True)
        value = sys.stdin.readline()
        if not value:
            return None
        return value.strip()
