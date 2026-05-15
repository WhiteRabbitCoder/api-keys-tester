# Features & Roadmap

## ✅ Completed Features

### Core Functionality
- [x] Multi-provider API key testing (5 providers)
- [x] Dynamic model listing per provider
- [x] Liveness testing with latency measurement
- [x] Beautiful terminal UI with Textual
- [x] Auto-detection of provider from key prefix
- [x] Full async/non-blocking operations
- [x] Keyboard-first navigation
- [x] Clear error messages for failed operations

### Providers
- [x] OpenAI (native API)
- [x] Google Gemini (unique API shape)
- [x] DeepSeek (OpenAI-compatible)
- [x] OpenRouter (OpenAI-compatible)
- [x] NVIDIA NIM (OpenAI-compatible)

### UI/UX
- [x] Provider dropdown with auto-detection
- [x] Password-masked API key input
- [x] Dynamic models list
- [x] Loading spinners during API calls
- [x] Real-time result display (status, latency, response)
- [x] Responsive two-pane layout (40/60 split)
- [x] Beautiful color scheme with Textual CSS

### Code Quality
- [x] Clean architecture (providers independent of UI)
- [x] DRY principle (OpenAI-compatible mixin)
- [x] Type hints with pydantic v2
- [x] Comprehensive error handling
- [x] Test verification script
- [x] Full documentation

---

## 🔄 Planned Features (Priority Order)

### Phase 1: Data Persistence (Medium Priority)
- [ ] Save test results to SQLite database
  - Store: provider, key (hashed), model, response, latency, timestamp
  - Query: view test history, compare latency across providers
- [ ] CSV export of test results
- [ ] JSON export for scripting/reporting

**Why**: Users may want to track performance over time and compare providers.

### Phase 2: Enhanced Testing (Medium Priority)
- [ ] Custom prompt input (currently hardcoded: "Say hello in one word")
- [ ] Prompt templates (greeting, reasoning, math, coding)
- [ ] Streaming response display (for longer outputs)
- [ ] Token count estimation (if provider supports)

**Why**: More flexible testing scenarios, better understanding of model capabilities.

### Phase 3: Multi-Key Comparison (Low Priority)
- [ ] Side-by-side testing of multiple keys simultaneously
- [ ] Latency comparison chart
- [ ] Cost-per-token comparison (where available)
- [ ] Ranked results table

**Why**: Power users comparing different API accounts or tiers.

### Phase 4: Advanced Features (Low Priority)
- [ ] Key management: securely store/retrieve keys
- [ ] Key masking toggle: show/hide API key
- [ ] Test scheduling: automated periodic tests
- [ ] Webhook integration: notify on key failure
- [ ] Rate limit tracking: detect and warn about rate limiting

**Why**: Enterprise/DevOps use cases.

### Phase 5: UI/UX Polish (Ongoing)
- [ ] Theme customization (dark/light mode)
- [ ] Configurable layouts
- [ ] Keyboard shortcuts cheat sheet (F1 help)
- [ ] Session persistence (remember last provider/key)
- [ ] Copy-to-clipboard for results

**Why**: Better user experience, accessibility.

---

## 🐛 Known Issues & TODOs

### Minor
- [ ] DeepSeek/OpenAI key ambiguity — currently defaults to OpenAI, user can override
- [ ] Some providers may return models without full metadata (handled gracefully)
- [ ] Long model names may wrap awkwardly in narrow terminals (graceful degradation)

### Future Improvements
- [ ] Provider-specific configuration (e.g., OpenAI org ID, custom endpoint)
- [ ] Batch testing: load multiple keys from CSV and test all
- [ ] Performance profiling: compare cold start vs warm latency
- [ ] Retry logic with exponential backoff (currently: fail once and retry manually)

---

## 🔧 Technical Debt (None Currently)

The codebase is clean and maintainable. No current technical debt identified.

### Architecture Notes for Future Developers
- **Providers**: Subclass `BaseProvider`, implement `list_models()` and `test_key()`. Use `OpenAICompatMixin` if API is OpenAI-compatible.
- **UI**: Use Textual's `Message` events for widget-to-screen communication. Avoid direct widget manipulation from other widgets.
- **Async**: All provider calls use `httpx.AsyncClient`. Use `run_worker()` to call them from Textual event handlers.
- **Key Detection**: Add new detection rules in `src/utils/key_detector.py` for new providers.

---

## 🌟 Community Contributions Welcome

Ideas for contributors:
1. Add a new provider (Anthropic Claude, Cohere, Mistral, etc.)
2. Implement result persistence (SQLite or JSON)
3. Add configuration file support (.apikeys.env or config.toml)
4. Write integration tests with mock API responses
5. Create a web API wrapper (FastAPI) for programmatic access

---

## Dependencies & Version Lock

Current stack is stable:
- Textual 0.61+ (released Sept 2024)
- httpx 0.27+ (released Dec 2024)
- pydantic 2.6+ (released Dec 2023)

Future updates should be backwards-compatible unless major version bumps required.
