"""Results panel widget for displaying test results."""

from textual.widgets import Static, Label, Button, LoadingIndicator, TextArea
from textual.containers import Vertical
from textual.message import Message
from src.providers.base import TestResult


class ResultsPanel(Static):
    """Right pane bottom: test results display."""

    class TestRequested(Message):
        """Message sent when user requests a liveness test."""

        pass

    def compose(self):
        """Compose child widgets."""
        with Vertical():
            yield Label("Test Results")
            yield Button("Run Liveness Test", id="btn-test", variant="success")
            yield LoadingIndicator(id="test-loading")
            yield Label("", id="result-status")
            yield Label("", id="result-latency")
            yield TextArea(read_only=True, id="result-response", language="text")

    def on_mount(self) -> None:
        """Hide the loading indicator on mount."""
        loading: LoadingIndicator = self.query_one("#test-loading", LoadingIndicator)
        loading.display = False
        test_btn: Button = self.query_one("#btn-test", Button)
        test_btn.disabled = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-test":
            self.post_message(self.TestRequested())

    def show_loading(self) -> None:
        """Show the loading indicator."""
        loading: LoadingIndicator = self.query_one("#test-loading", LoadingIndicator)
        loading.display = True

    def hide_loading(self) -> None:
        """Hide the loading indicator."""
        loading: LoadingIndicator = self.query_one("#test-loading", LoadingIndicator)
        loading.display = False

    def show_result(self, result: TestResult) -> None:
        """Display test result."""
        self.hide_loading()

        status_label: Label = self.query_one("#result-status", Label)
        latency_label: Label = self.query_one("#result-latency", Label)
        response_area: TextArea = self.query_one("#result-response", TextArea)

        if result.success:
            status_label.update("✓ Valid")
            status_label.remove_class("invalid")
            status_label.add_class("valid")
        else:
            status_label.update("✗ Invalid")
            status_label.remove_class("valid")
            status_label.add_class("invalid")

        latency_label.update(f"Latency: {result.latency_ms:.1f}ms")

        response_text = result.response_text or result.error_message or "No response"
        response_area.text = response_text

    def show_error(self, error: str) -> None:
        """Display an error."""
        self.hide_loading()

        status_label: Label = self.query_one("#result-status", Label)
        status_label.update("✗ Error")
        status_label.remove_class("valid")
        status_label.add_class("invalid")

        response_area: TextArea = self.query_one("#result-response", TextArea)
        response_area.text = error

    def enable_test_button(self) -> None:
        """Enable the test button."""
        test_btn: Button = self.query_one("#btn-test", Button)
        test_btn.disabled = False

    def disable_test_button(self) -> None:
        """Disable the test button."""
        test_btn: Button = self.query_one("#btn-test", Button)
        test_btn.disabled = True

    def clear(self) -> None:
        """Clear all results."""
        status_label: Label = self.query_one("#result-status", Label)
        latency_label: Label = self.query_one("#result-latency", Label)
        response_area: TextArea = self.query_one("#result-response", TextArea)

        status_label.update("")
        latency_label.update("")
        response_area.text = ""

        status_label.remove_class("valid")
        status_label.remove_class("invalid")

        self.disable_test_button()
        self.hide_loading()
