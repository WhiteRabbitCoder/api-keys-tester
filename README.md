# 🔑 API Keys Tester

A beautiful, interactive terminal application to test and validate AI provider API keys. Works on **macOS, Linux, and Windows**. No complicated setup—just download, install, and run!

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-WhiteRabbitCoder/api--keys--tester-blue)](https://github.com/WhiteRabbitCoder/api-keys-tester)

## ✨ Features

- **5 AI Providers Supported**:
  - 🟠 OpenAI (GPT-4, GPT-3.5, o1, etc.)
  - 🔵 Google Gemini (Gemini 2.0, 1.5, etc.)
  - ⚡ DeepSeek (All models)
  - 🌍 OpenRouter (1000+ models)
  - 🟣 NVIDIA NIM (Local/cloud models)

- **What it Does**:
  1. ✅ Validates your API key
  2. 📋 Lists all available models for your account
  3. ⚡ Tests response time with a live API call
  4. 📊 Shows detailed results (latency, response, status)

- **Beautiful Terminal UI**:
  - 🎨 Clean, modern design
  - ⌨️ Full keyboard navigation
  - 🚀 Smooth, non-blocking operations
  - 🎯 Real-time loading indicators

## 🚀 Quick Start (2 Minutes)

### Step 1: Install Python (if needed)

Check if you have Python 3.12+:
```bash
python3 --version
```

If not, [download Python 3.12+](https://www.python.org/downloads/)

### Step 2: Clone the Repository

```bash
git clone https://github.com/WhiteRabbitCoder/api-keys-tester.git
cd api-keys-tester
```

### Step 3: Set Up (One-Time)

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell):**
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 4: Run the App

```bash
python main.py
```

You should see a beautiful terminal interface! 🎉

## 📖 How to Use

### Testing Your First API Key

1. **Copy your API key** from your provider's dashboard:
   - OpenAI: https://platform.openai.com/account/api-keys
   - Google Gemini: https://aistudio.google.com/app/apikey
   - DeepSeek: https://platform.deepseek.com/account/api_keys
   - OpenRouter: https://openrouter.ai/keys
   - NVIDIA NIM: https://build.nvidia.com/

2. **Select Provider** (or let the app auto-detect):
   - The app recognizes key prefixes automatically
   - Can override manually if needed

3. **Paste Your Key** in the input field:
   - The key is masked (won't show on screen)
   - Just paste and press Enter or click "Fetch Models"

4. **View Available Models**:
   - All models for your account appear instantly
   - Shows model names and IDs

5. **Select a Model** and click "Run Liveness Test":
   - Sends: "Say hello in one word."
   - Shows: Response + latency (usually 200-1000ms)
   - Confirms: Your key works! ✓

### Keyboard Navigation

| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Move between fields |
| `↑` `↓` | Navigate lists |
| `Enter` | Confirm / Select |
| `Ctrl+C` | Exit app |

## 🔑 Supported API Keys

| Provider | Key Format | Example |
|----------|-----------|---------|
| OpenAI | Starts with `sk-` | `sk-proj-abc123...` |
| Gemini | Starts with `AIza` | `AIzaSyDiT-abc123...` |
| DeepSeek | Starts with `sk-` | `sk-abc123...` |
| OpenRouter | Starts with `sk-or-` | `sk-or-abc123...` |
| NVIDIA NIM | Starts with `nvapi-` | `nvapi-abc123...` |

**Pro Tip**: The app auto-detects your provider from the key prefix. If it guesses wrong, just select the correct one from the dropdown.

## 🛠️ Troubleshooting

### "Invalid API key" Error
- ✓ Check your key has no extra spaces
- ✓ Verify it's still valid in your provider's console
- ✓ Make sure API access is enabled

### No Models Appear
- ✓ Check your internet connection
- ✓ Your key may lack required permissions
- ✓ Try again (some providers have rate limits)

### Slow/Timeout
- ✓ Check if the provider's API is slow
- ✓ Some providers respond slower than others
- ✓ Try a different provider to compare

### Python/pip Issues on Windows
If you get errors, try using `python` instead of `python3`:
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## 📦 What's Installed

The app uses only 5 core dependencies:
- **textual** — Beautiful terminal UI framework
- **httpx** — Async HTTP client for API calls
- **pydantic** — Data validation
- **python-dotenv** — Environment variable support
- **rich** — Terminal formatting

Everything is lightweight and has no external dependencies beyond these.

## 📚 More Information

- **[QUICKSTART.md](QUICKSTART.md)** — 5-minute guided tour
- **[FEATURES.md](FEATURES.md)** — Roadmap and planned features
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** — Technical details

## 🧪 Verify Installation

Before testing with real keys, you can verify everything is set up correctly:

```bash
source .venv/bin/activate  # Activate virtual environment
python test_providers.py
```

You should see:
```
✓ All 5 providers imported
✓ Key detection working
✓ Provider interfaces correct
```

## 🤝 Contributing

Want to add a new provider or feature? We'd love contributions!

### Adding a New Provider

1. Create a file `src/providers/myservice_provider.py`
2. Subclass `BaseProvider` and implement two methods:
   - `list_models(api_key)` — return available models
   - `test_key(api_key, model_id)` — run a test prompt
3. Add to `src/providers/__init__.py`
4. Update key detection in `src/utils/key_detector.py`

See existing providers for examples!

## 📋 Requirements

- **Python**: 3.12 or higher
- **OS**: macOS, Linux, Windows
- **Internet**: Required to call provider APIs
- **Terminal**: Any modern terminal (works in VS Code, iTerm, Windows Terminal, etc.)

## 🎯 Use Cases

✅ **Verify API Keys Work** — Before using in production  
✅ **Compare Latency** — See which provider is fastest  
✅ **Check Model Availability** — What models do you have access to?  
✅ **Test Multiple Keys** — Validate different accounts  
✅ **Quick API Diagnostics** — Is the service up?

## 📄 License

MIT License — Free to use, modify, and distribute!

## 🙋 Support

**Having issues?** Check:
1. [QUICKSTART.md](QUICKSTART.md) — Step-by-step guide
2. [Troubleshooting](#-troubleshooting) section above
3. [GitHub Issues](https://github.com/WhiteRabbitCoder/api-keys-tester/issues)

## 🌟 Star This Repo!

If this tool saves you time, please give it a ⭐ on GitHub!

---

**Built with** ❤️ using Python + Textual  
**Author**: Angelo Gaviria  
**Repository**: https://github.com/WhiteRabbitCoder/api-keys-tester
