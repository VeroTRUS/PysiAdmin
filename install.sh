#!/usr/bin/env bash
# PysiAdmin — install.sh
# Tested on Fedora 45, kernel 7.0.0-rc7
set -euo pipefail

echo "=== PysiAdmin Installer ==="

# ── System packages ──────────────────────────────────────────────────────────
sudo dnf install -y \
    python3 python3-pip python3-venv \
    gcc make \
    bcc bcc-tools python3-bcc \
    kernel-devel

# ── Python venv ───────────────────────────────────────────────────────────────
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ── Build native helper ───────────────────────────────────────────────────────
make -C native

# ── Bootstrap config files ───────────────────────────────────────────────────
if [[ ! -f .env ]]; then
    echo 'DISCORD_BOT_TOKEN=YOUR_TOKEN_HERE' > .env
    echo "[!] .env created — paste your bot token."
fi

if [[ ! -f pysi-config.json ]]; then
    python3 -c "from config.settings import Settings; Settings.load()"
fi

echo ""
echo "=== Done. Next steps: ==="
echo "  1.  Edit .env          → set DISCORD_BOT_TOKEN"
echo "  2.  Edit pysi-config.json → add your Discord user ID to owner_ids"
echo "  3.  source .venv/bin/activate"
echo "  4.  python3 pysi_admin.py"
echo ""
echo "Optional eBPF tracer (separate terminal, needs root):"
echo "  sudo .venv/bin/python3 ebpf/monitor.py"
