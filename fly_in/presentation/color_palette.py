"""Resolve map color names with webcolors for ANSI terminal output."""
import webcolors


class ColorPalette:
    """Color movement tokens without restricting accepted map color names."""

    def __init__(self, enabled: bool) -> None:
        """Remember whether colored output is wanted."""
        self.enabled = enabled

    def paint(self, text: str, color: str = 'cyan') -> str:
        """Resolve CSS3 colors, falling back to white for custom names."""
        if not self.enabled:
            return text
        try:
            red, green, blue = webcolors.name_to_rgb(color.lower())
        except ValueError:
            red, green, blue = 255, 255, 255
        return f'\033[38;2;{red};{green};{blue}m{text}\033[0m'
