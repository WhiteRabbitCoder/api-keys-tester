# API Keys Testing TUI

An interactive terminal UI application to test and validate AI provider API keys. Built with Python and Textual.

## Features

- **Multi-provider support**: Test keys for OpenAI, Google Gemini, DeepSeek, OpenRouter, and NVIDIA NIM
- **Dynamic model listing**: Automatically fetches and displays available models for each provider
- **Liveness testing**: Run a simple prompt test to verify API key validity and measure latency
- **Beautiful TUI**: Clean, keyboard-navigable interface with real-time feedback
- **Auto-detection**: Automatically detects provider from API key prefix (with manual override)

## Installation

### Prerequisites
- Python 3.12+

### Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Activate virtual environment (if not already activated)
source .venv/bin/activate

# Run the application
python main.py
```

### Keyboard Navigation

- **Tab** / **Shift+Tab**: Navigate between widgets
- **Arrow Keys**: Select options or navigate lists
- **Enter**: Confirm selection or trigger action
- **Esc**: (future) Cancel operations
- **Ctrl+C**: Quit the application

### Workflow

1. **Select Provider**: The left panel starts with a provider dropdown (defaults to OpenAI, auto-detects from key prefix)
2. **Enter API Key**: Paste or type your API key in the input field
3. **Fetch Models**: Click "Fetch Models" to retrieve available models for your key
4. **Select Model**: Choose a model from the list on the right
5. **Run Test**: Click "Run Liveness Test" to verify the key works and see response latency

## Supported Providers

| Provider | Key Prefix | Status |
|----------|-----------|--------|
| OpenAI | `sk-` | ✓ Implemented |
| Google Gemini | `AIza` | ✓ Implemented |
| DeepSeek | `sk-` | ✓ Implemented |
| OpenRouter | `sk-or-` | ✓ Implemented |
| NVIDIA NIM | `nvapi-` | ✓ Implemented |

## Project Structure

```
src/
├── providers/           # API provider implementations
│   ├── base.py         # Abstract base class and data models
│   ├── openai_provider.py
│   ├── gemini_provider.py
│   ├── deepseek_provider.py
│   ├── openrouter_provider.py
│   ├── nvidia_nim_provider.py
│   └── openai_compat_mixin.py  # Shared mixin for OpenAI-compatible APIs
├── tui/                 # Textual UI components
│   ├── app.py          # Main application root
│   ├── tui.tcss        # Styling (Textual CSS)
│   ├── screens/        # Screen definitions
│   │   └── main_screen.py
│   └── widgets/        # Custom widgets
│       ├── key_panel.py
│       ├── models_panel.py
│       └── results_panel.py
└── utils/              # Utilities
    └── key_detector.py # Key prefix detection
```

## Architecture

### Data Layer (Providers)

Each provider is a subclass of `BaseProvider` with two async methods:

- `list_models(api_key: str) -> list[ModelInfo]`: Fetch available models
- `test_key(api_key: str, model_id: str) -> TestResult`: Run a liveness test

Providers are completely independent of the UI and can be used programmatically.

### UI Layer (Textual)

The TUI is structured as:

- **MainScreen**: Event bus and state manager
- **KeyPanel**: Provider selection and key input (left pane)
- **ModelsPanel**: Available models list (right pane, top)
- **ResultsPanel**: Test results display (right pane, bottom)

Widgets communicate via Textual `Message` events, keeping UI and business logic decoupled.

## Development Notes

### Adding a New Provider

1. Create a new file in `src/providers/` (e.g., `myservice_provider.py`)
2. Subclass `BaseProvider` and implement `list_models()` and `test_key()`
3. Add an instance to the `PROVIDERS` dict in `src/providers/__init__.py`
4. Update key detection in `src/utils/key_detector.py` if applicable

### Key Detection

The `detect_provider()` function uses key prefixes to infer the provider. Some providers (e.g., DeepSeek and OpenAI) share prefixes — in these cases, the UI allows manual override.

## Dependencies

- **textual**: TUI framework with built-in widgets
- **httpx**: Async HTTP client for API calls
- **pydantic**: Data validation for API responses
- **python-dotenv**: Environment variable loading (for future .env support)
- **rich**: Terminal formatting (included with textual)

## Future Enhancements

- [ ] Persist tested keys with metadata (timestamp, model used, latency)
- [ ] Multi-key comparison: test multiple keys side-by-side
- [ ] Custom prompt input for tests
- [ ] Export results to CSV/JSON
- [ ] Theme customization
- [ ] Streaming response display for longer outputs
- [ ] Key masking toggle (show/hide)

## Troubleshooting

### "Invalid API key" error
- Verify the key is entered correctly and has no extra spaces
- Check that the API key is still valid in the provider's console
- Ensure you have API access enabled for the provider

### No models appear
- Check your internet connection
- Verify the API key has sufficient permissions
- Some providers may not return models for certain key types

### Timeout errors
- Check your network connection
- The API might be slow; try again
- Some providers have rate limiting; wait a moment before retrying

## License

MIT

## Author

Angelo Gaviria
