# 🔥 BTC Cross-Matrix Puzzle Scanner v20.0

> **Secure Edition** - No hardcoded secrets, reads from Environment Variables

## 📋 Features

- ✅ **Secure**: No hardcoded tokens (reads from `.env` or Environment Variables)
- ✅ **Auto WIF**: Generates WIF automatically on match
- ✅ **Telegram Reports**: Real-time progress updates every 60 seconds
- ✅ **Auto-Resume**: Saves checkpoint and resumes automatically
- ✅ **Parallel Processing**: Uses all CPU cores via ProcessPoolExecutor
- ✅ **8001 Magic Points**: 81 base + 7920 intermediate points
- ✅ **±1000 Step Range**: Searches around each magic point
- ✅ **91 Puzzles**: Targets puzzles #70 through #160

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/engmuradghannam-dot/MuradEngine.git
cd MuradEngine
pip install -r requirements.txt
```

### 2. Configure Telegram (Required)

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your tokens:

```env
TELEGRAM_BOT_TOKEN=8678763407:AAHovW-mT3dA1j04NLe0JzNidRQZw9DIc-c
TELEGRAM_CHAT_ID=6221148602
```

**⚠️ NEVER commit `.env` to GitHub!**

### 3. Run

```bash
python btc_cross_matrix_scanner_v20_secure.py
```

## 🔒 Security

### Local Development
- Use `.env` file (already in `.gitignore`)
- `.env` is NEVER committed to Git

### GitHub Actions (CI/CD)
- Go to: `Settings → Secrets and variables → Actions`
- Add:
  - `TELEGRAM_BOT_TOKEN` = your bot token
  - `TELEGRAM_CHAT_ID` = your chat ID
- The workflow reads from GitHub Secrets automatically

### Telegram Bot Setup
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot: `/newbot`
3. Get your token
4. Message your bot to get your `chat_id`

## 📊 Performance

| Backend | Speed (1 core) | Speed (8 cores) | Total Time |
|---------|---------------|-----------------|------------|
| coincurve (C) | ~50,000/sec | ~400,000/sec | ~2.5 hours |
| ecdsa (Python) | ~500/sec | ~4,000/sec | ~10 days |

**Recommendation**: Use Python 3.12 with `coincurve` for maximum speed.

## 📁 Output Files

| File | Description |
|------|-------------|
| `scanner_v20_matches.txt` | Full match details with WIF |
| `scanner_v20_wif_keys.txt` | WIF keys only (wallet import) |
| `scanner_v20_checkpoint.json` | Resume checkpoint |

## 🐛 Troubleshooting

### "TELEGRAM_BOT_TOKEN not set"
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### "coincurve not found"
```bash
pip install coincurve
```

### Slow speed
- Install `coincurve`: `pip install coincurve`
- Use Python 3.12 (faster than 3.14)
- Run on Google Colab for free GPU/CPU

## 📱 Telegram Notifications

You'll receive:
- 🚀 **Startup**: Backend, workers, total keys
- 📊 **Progress**: Every 60 seconds
- 🎉 **Match**: Private key + WIF immediately
- 🏁 **Completion**: Summary + files

## ⚖️ License

For educational purposes only.

---

**Made with 🔥 by Murad**
