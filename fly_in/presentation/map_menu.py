"""Interactive selection of supplied maps and custom map files."""
import sys
from pathlib import Path

from fly_in.presentation.color_palette import ColorPalette


class MapMenu:
    """Choose a supplied map or a custom path interactively."""

    def __init__(self, palette: ColorPalette) -> None:
        """Locate supplied maps relative to the application, not the cwd."""
        self.palette = palette
        root = Path(__file__).resolve().parents[2] / 'maps'
        self.maps = [path for level in ('easy', 'medium', 'hard', 'challenger')
                     for path in sorted((root / level).glob('*.txt'))]

    def choose(self) -> Path | None:
        """Display maps and retry invalid choices until EOF or quit."""
        border = '  +' + '-' * 44 + '+'
        title = '\n'.join(('', border,
                           f'  |{"F L Y - I N":^44}|',
                           f'  |{"DRONE ROUTING SIMULATOR":^44}|',
                           border, '  MAP SELECTION'))
        print(self.palette.paint(title, 'cyan'), file=sys.stderr)
        previous = ''
        for index, path in enumerate(self.maps, 1):
            if path.parent.name != previous:
                previous = path.parent.name
                label = previous.upper()
                if previous == 'challenger':
                    label += ' (optional)'
                print(f'\n  {label}', file=sys.stderr)
            label = path.stem.replace('_', ' ')
            print(f'  {index:2}. {label}', file=sys.stderr)
        print('\n  p. Custom map path\n  q. Quit', file=sys.stderr)
        while True:
            choice = self._read('\n  Select map: ')
            if choice is None or choice.lower() == 'q':
                return None
            if choice.lower() == 'p':
                custom = self._read('  Map path: ')
                if custom:
                    return Path(custom).expanduser()
            elif choice.isascii() and choice.isdecimal():
                # Compare strings first to avoid huge integer input conversion.
                if len(choice) <= 6 and 1 <= int(choice) <= len(self.maps):
                    return self.maps[int(choice) - 1]
            print('  Invalid choice. Enter a map number, p or q.',
                  file=sys.stderr)

    def _read(self, prompt: str) -> str | None:
        """Read input without putting prompts into the movement stream."""
        print(prompt, end='', file=sys.stderr, flush=True)
        value = sys.stdin.readline()
        return value.strip() if value else None
