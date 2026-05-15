"""Key panel widget for provider selection and API key input."""

from textual.widgets import Static, Label, Select, Input, Button
from textual.containers import Vertical
from textual.message import Message
from src.providers import all_providers
from src.utils.key_detector import detect_provider


class KeyPanel(Static):
    """Left pane: provider selection and API key input."""

    class FetchRequested(Message):
        """Message sent when user requests to fetch models."""

        def __init__(self, provider: str, api_key: str) -> None:
            super().__init__()
            self.provider = provider
            self.api_key = api_key

    def compose(self):
        """Compose child widgets."""
        with Vertical():
            yield Label("Provider")
            yield Select(
                options=[(name, name) for name in all_providers()],
                id="provider-select",
                value=all_providers()[0],
            )
            yield Label("API Key")
            yield Input(
                id="key-input",
                password=True,
                placeholder="Enter your API key...",
            )
            yield Label("", id="key-status")
            yield Button("Fetch Models", id="btn-fetch", variant="primary")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Auto-detect provider from key prefix."""
        if event.input.id == "key-input":
            api_key = event.value.strip()
            if api_key:
                detected = detect_provider(api_key)
                if detected:
                    select_widget: Select = self.query_one("#provider-select", Select)
                    if select_widget.value != detected:
                        select_widget.value = detected
                self.clear_status()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input field."""
        if event.input.id == "key-input":
            self._handle_fetch()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-fetch":
            self._handle_fetch()

    def _handle_fetch(self) -> None:
        """Fetch models for the selected provider."""
        select_widget: Select = self.query_one("#provider-select", Select)
        input_widget: Input = self.query_one("#key-input", Input)

        provider = str(select_widget.value)
        api_key = input_widget.value.strip()

        if not api_key:
            self.show_error("Please enter an API key")
            return

        self.post_message(self.FetchRequested(provider, api_key))

    def show_error(self, message: str) -> None:
        """Display an error message."""
        label: Label = self.query_one("#key-status", Label)
        label.update(f"❌ {message}")
        label.remove_class("success")
        label.add_class("error")

    def show_success(self, message: str) -> None:
        """Display a success message."""
        label: Label = self.query_one("#key-status", Label)
        label.update(f"✓ {message}")
        label.remove_class("error")
        label.add_class("success")

    def clear_status(self) -> None:
        """Clear the status label."""
        label: Label = self.query_one("#key-status", Label)
        label.update("")
        label.remove_class("error")
        label.remove_class("success")
