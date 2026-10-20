"""Color terminal text using CSS names and ANSI RGB escape codes."""

import webcolors


class ColorPalette:
    """Apply terminal colors without restricting accepted map color names."""

    def __init__(
        self,
        enabled: bool
    ) -> None:
        """Remember whether colored output is wanted."""
        self.enabled = enabled

    def paint(
        self,
        text: str,
        color: str = 'cyan'
    ) -> str:
        """Color text and reset the terminal; use white for unknown names."""
        if not self.enabled:
            return text

        if color.lower() == 'rainbow':
            colors = ('red', 'orange', 'yellow', 'green', 'blue', 'indigo',
                      'violet')
            result = ''
            for index, character in enumerate(text):
                name = colors[index % len(colors)]
                result += self.paint(character, name)
            return result

        try:
            rgb = webcolors.name_to_rgb(color.lower())
        except ValueError:
            rgb = webcolors.name_to_rgb('white')

        code = f'\033[38;2;{rgb.red};{rgb.green};{rgb.blue}m'
        return f'{code}{text}\033[0m'
