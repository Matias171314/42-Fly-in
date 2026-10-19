"""Color terminal text using standard ANSI escape codes."""


class ColorPalette:
    """Apply terminal colors without restricting accepted map color names."""

    COLORS: dict[str, str] = {
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'gray': '\033[90m',
        'grey': '\033[90m',
        'orange': '\033[33m',
        'gold': '\033[33m',
        'brown': '\033[33m',
        'purple': '\033[35m',
        'violet': '\033[35m',
        'lime': '\033[92m',
        'darkred': '\033[31m',
        'maroon': '\033[31m',
        'crimson': '\033[91m',
    }

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
        code = self.COLORS.get(color.lower(), self.COLORS['white'])
        return f'{code}{text}\033[0m'
