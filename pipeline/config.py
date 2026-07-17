"""
config.py — All the knobs in one place.

Person B: change thresholds here without touching agent code.
The fuzzy threshold and model names are the ones you'll actually tune.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── API keys ────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# ── Models ──────────────────────────────────────────────────────────────
# Main model for Pro/Con/Judge reasoning. Instruction-following matters
# more than raw speed here, so use Sonnet.
MODEL_MAIN = "claude-sonnet-4-6"

# Fast model for the fast-path provisional verdict (Person A owns this,
# but exposing here in case B needs it for anything cheap).
MODEL_FAST = "claude-haiku-4-5"

# ── Fuzzy-match threshold ───────────────────────────────────────────────
# Below this ratio (0-100), a "paraphrased" quote is rejected.
# Empirically calibrated — tune during setup with 5-10 real quote/page pairs.
FUZZY_THRESHOLD = 85

# ── Search + fetch limits ───────────────────────────────────────────────
SEARCH_MAX_RESULTS = 8       # per search() call
FETCH_TIMEOUT_SECONDS = 8    # httpx timeout when pulling a page
FETCH_MAX_BYTES = 2_000_000  # 2 MB safety limit per page

# ── Cache location ──────────────────────────────────────────────────────
# Shared with Person D's cache harness. Coordinate on this path at hour 0.
CACHE_DIR = Path(os.getenv("PRISM_CACHE_DIR", "/tmp/prism_cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── Reddit ──────────────────────────────────────────────────────────────
# Reddit's public JSON requires a descriptive User-Agent or you get 429'd.
REDDIT_USER_AGENT = "Prism-HackwithSeattle/1.0"

# ── Debug ───────────────────────────────────────────────────────────────
DEBUG = os.getenv("PRISM_DEBUG", "0") == "1"
