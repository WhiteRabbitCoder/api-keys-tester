"""Main screen for the API Keys Testing TUI."""

from typing import Optional
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from src.providers import get_provider, ModelInfo, ProviderError
from src.tui.widgets.key_panel import KeyPanel
from src.tui.widgets.models_panel import ModelsPanel
from src.tui.widgets.results_panel import ResultsPanel


class MainScreen(Screen):
    """Main screen with two-pane layout: key input (left) and results (right)."""

    current_provider: reactive[Optional[str]] = reactive(None)
    current_api_key: reactive[Optional[str]] = reactive(None)
    current_model: reactive[Optional[ModelInfo]] = reactive(None)

    def compose(self):
        """Compose the main layout."""
        with Horizontal(id="main-layout"):
            yield KeyPanel(id="key-panel")
            with Vertical(id="right-pane"):
                yield ModelsPanel(id="models-panel")
                yield ResultsPanel(id="results-panel")

    def on_key_panel_fetch_requested(self, event: KeyPanel.FetchRequested) -> None:
        """Handle fetch models request."""
        self.current_provider = event.provider
        self.current_api_key = event.api_key
        self.current_model = None

        key_panel: KeyPanel = self.query_one("#key-panel", KeyPanel)
        models_panel: ModelsPanel = self.query_one("#models-panel", ModelsPanel)
        results_panel: ResultsPanel = self.query_one("#results-panel", ResultsPanel)

        models_panel.show_loading()
        results_panel.clear()

        self.run_worker(self._fetch_models_async(event.provider, event.api_key), exclusive=True)

    async def _fetch_models_async(self, provider_name: str, api_key: str) -> None:
        """Async worker to fetch models."""
        key_panel: KeyPanel = self.query_one("#key-panel", KeyPanel)
        models_panel: ModelsPanel = self.query_one("#models-panel", ModelsPanel)
        results_panel: ResultsPanel = self.query_one("#results-panel", ResultsPanel)

        try:
            provider = get_provider(provider_name)
            models = await provider.list_models(api_key)
            models_panel.populate(models)
            models_panel.hide_loading()
            key_panel.show_success(f"{len(models)} model(s) available")
            results_panel.clear()
        except ProviderError as e:
            models_panel.hide_loading()
            models_panel.clear()
            key_panel.show_error(str(e))
            results_panel.clear()
        except Exception as e:
            models_panel.hide_loading()
            models_panel.clear()
            key_panel.show_error(f"Error: {e}")
            results_panel.clear()

    def on_models_panel_model_selected(self, event: ModelsPanel.ModelSelected) -> None:
        """Handle model selection."""
        self.current_model = event.model
        results_panel: ResultsPanel = self.query_one("#results-panel", ResultsPanel)
        results_panel.clear()

    def on_results_panel_test_requested(self, event: ResultsPanel.TestRequested) -> None:
        """Handle liveness test request."""
        results_panel: ResultsPanel = self.query_one("#results-panel", ResultsPanel)

        if not self.current_model:
            results_panel.show_error("❌ Please select a model first")
            return

        if not self.current_api_key or not self.current_provider:
            results_panel.show_error("❌ Please enter API key and select a provider first")
            return

        results_panel.show_loading()

        self.run_worker(
            self._run_test_async(
                self.current_provider,
                self.current_api_key,
                self.current_model.id,
            ),
            exclusive=True,
        )

    async def _run_test_async(self, provider_name: str, api_key: str, model_id: str) -> None:
        """Async worker to run the liveness test."""
        results_panel: ResultsPanel = self.query_one("#results-panel", ResultsPanel)

        try:
            provider = get_provider(provider_name)
            result = await provider.test_key(api_key, model_id)
            results_panel.show_result(result)
        except ProviderError as e:
            results_panel.show_error(f"Test failed: {e}")
        except Exception as e:
            results_panel.show_error(f"Unexpected error: {e}")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
