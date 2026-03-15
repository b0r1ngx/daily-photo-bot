"""Root conftest — sets required env vars before any src imports."""
import os

# Provide dummy values for required env vars so settings.py doesn't sys.exit(1) during tests
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token-for-ci")
os.environ.setdefault("PEXELS_API_KEY", "test-pexels-key-for-ci")
