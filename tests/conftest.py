import os

# Deterministic by default: demo prices, no LLM. Live paths are tested with mocks in test_live.py.
os.environ["LIVE_DATA"] = "0"
os.environ["OPENROUTER_API_KEY"] = ""
