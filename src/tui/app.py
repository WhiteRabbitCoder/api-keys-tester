"""Main Textual application."""

from textual.app import ComposeResult
from textual.app import App
from textual.binding import Binding
from .screens.main_screen import MainScreen


class ApiKeysTesterApp(App):
    """API Keys Testing TUI Application."""

    CSS_PATH = "tui.tcss"
    TITLE = "API Keys Tester"
    SUBTITLE = "Test and validate AI provider API keys"

    BINDINGS = [
        Binding("tab", "focus_next", "Next", show=False),
        Binding("shift+tab", "focus_previous", "Previous", show=False),
    ]

    def on_mount(self) -> None:
        """Mount the main screen."""
        self.push_screen(MainScreen())


def run_app():
    """Run the TUI application."""
    app = ApiKeysTesterApp()
    app.run()


if __name__ == "__main__":
    run_app()
