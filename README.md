# Repo Starrer ⭐

Automatically star all repositories on a GitHub user's profile page.

## Quick Start

```bash
pip install playwright
playwright install chromium
python3 debug.py
```

**First run:** Browser opens → Sign into GitHub manually → Credentials saved
**Future runs:** Auto-logged in, starts starring immediately

## How It Works

Uses Playwright persistent profile to save GitHub login. Clicks star buttons via AJAX (no page reloads). Skips already-starred repos. Rate limited with 800ms delays.

**Profile location:** `~/Library/Application Support/pw-profiles/github.com`

## License

MIT
