# Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the App

```bash
python main.py
```

You'll see a beautiful terminal UI with:
- **Left pane**: Provider selector + API key input
- **Right pane top**: Available models list
- **Right pane bottom**: Test results

## Testing a Provider

### OpenAI Example

1. **Paste your OpenAI API key** (starts with `sk-`)
   - The app auto-detects "OpenAI" provider
   - Key input field accepts the key as-is (it's masked)

2. **Click "Fetch Models"** or press Enter
   - Loading indicator appears
   - Models list populates (gpt-4o, gpt-4-turbo, gpt-3.5-turbo, etc.)

3. **Select a model** (use arrow keys, press Enter)
   - Test button becomes enabled

4. **Click "Run Liveness Test"**
   - App sends: "Say hello in one word."
   - Shows response (typically "Hello" or "Hi")
   - Displays latency (typically 200-800ms)

### Google Gemini Example

1. **Paste a Gemini API key** (starts with `AIza`)
   - App auto-detects "Google Gemini"

2. **Fetch Models**
   - Lists: gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash, etc.

3. **Select & Test**
   - Same workflow as OpenAI

## Key Prefixes (Auto-Detection)

| Provider | Prefix | Example |
|----------|--------|---------|
| OpenAI | `sk-` | `sk-proj-abc123...` |
| Gemini | `AIza` | `AIzaSyDiT-abc123...` |
| DeepSeek | `sk-` | `sk-abc123...` |
| OpenRouter | `sk-or-` | `sk-or-abc123...` |
| NVIDIA NIM | `nvapi-` | `nvapi-abc123...` |

**Note**: DeepSeek shares the `sk-` prefix with OpenAI. If you paste a DeepSeek key, the app detects OpenAI by default — you can manually select "deepseek" from the dropdown.

## Troubleshooting

### "Invalid API key" error
- Double-check the key in your provider's dashboard
- Make sure you didn't accidentally add spaces or extra characters

### No models appear
- Check your internet connection
- Verify the API key has the right permissions
- Wait a moment and try again (rate limiting)

### App is slow to respond
- Some providers have slower API responses
- Try with a different provider to compare
- Check if your internet connection is stable

## Testing Without API Keys

To verify the app structure and imports work:

```bash
python test_providers.py
```

This checks that all providers are correctly configured without needing real keys.

## Next Steps

- Try different providers and compare latency
- Experiment with different models
- Check out the [README](README.md) for more details

## Support

The app is designed to be intuitive. Use Tab/Shift+Tab to navigate between fields, arrow keys to select from lists, and Enter to confirm actions.
