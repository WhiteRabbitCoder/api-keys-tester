"""Models panel widget for displaying available models."""

from textual.widgets import Static, Label, ListView, ListItem, LoadingIndicator
from textual.containers import Vertical
from textual.message import Message
from src.providers.base import ModelInfo


class ModelListItem(ListItem):
    """A list item for a model."""

    def __init__(self, model: ModelInfo) -> None:
        super().__init__(Label(model.id))
        self.model = model


class ModelsPanel(Static):
    """Right pane top: available models list."""

    class ModelSelected(Message):
        """Message sent when user selects a model."""

        def __init__(self, model: ModelInfo) -> None:
            super().__init__()
            self.model = model

    def compose(self):
        """Compose child widgets."""
        with Vertical():
            yield Label("Available Models")
            yield LoadingIndicator(id="models-loading")
            yield ListView(id="models-list")

    def on_mount(self) -> None:
        """Hide the loading indicator on mount."""
        loading: LoadingIndicator = self.query_one("#models-loading", LoadingIndicator)
        loading.display = False

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle model selection."""
        item = event.cursor_line
        list_view: ListView = self.query_one("#models-list", ListView)
        if item < len(list_view.children):
            selected_item = list_view.children[item]
            if isinstance(selected_item, ModelListItem):
                self.post_message(self.ModelSelected(selected_item.model))

    def populate(self, models: list[ModelInfo]) -> None:
        """Populate the list with models."""
        list_view: ListView = self.query_one("#models-list", ListView)
        list_view.clear()
        for model in models:
            list_view.append(ModelListItem(model))

    def show_loading(self) -> None:
        """Show the loading indicator."""
        loading: LoadingIndicator = self.query_one("#models-loading", LoadingIndicator)
        loading.display = True

    def hide_loading(self) -> None:
        """Hide the loading indicator."""
        loading: LoadingIndicator = self.query_one("#models-loading", LoadingIndicator)
        loading.display = False

    def clear(self) -> None:
        """Clear the models list."""
        list_view: ListView = self.query_one("#models-list", ListView)
        list_view.clear()
        self.hide_loading()
