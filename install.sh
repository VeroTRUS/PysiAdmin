#!/usr/bin/env sh
# PysiAdmin install.sh — Linux + BSD
# Detects OS automatically.
set -e

OS="$(uname -s)"

echo "=== PysiAdmin Installer ==="
echo "Detected OS: $OS"

case "$OS" in

  Linux)
    # Detect distro
    if   command -v dnf     >/dev/null 2>&1; then
      sudo dnf install -y git gcc make python3 python3-pip bcc python3-bcc kernel-devel
    elif command -v apt-get >/dev/null 2>&1; then
      sudo apt-get update
      sudo apt-get install -y git gcc make python3 python3-pip python3-venv \
           bpfcc-tools python3-bpfcc "linux-headers-$(uname -r)"
    elif command -v pacman  >/dev/null 2>&1; then
      sudo pacman -S --needed git gcc make python python-pip \
           bcc bcc-tools python-bcc linux-headers
    elif command -v emerge  >/dev/null 2>&1; then
      sudo emerge --ask dev-vcs/git sys-devel/gcc sys-devel/make \
           dev-lang/python dev-util/bcc
    elif command -v zypper  >/dev/null 2>&1; then
      sudo zypper install -y git gcc make python3 python3-pip bcc bpftool
    elif command -v eopkg   >/dev/null 2>&1; then
      sudo eopkg install -y git gcc make python3 python3-pip kernel-headers
    else
      echo "[!] Unknown Linux distro — install git gcc make python3 python3-pip bcc manually."
    fi
    ;;

  FreeBSD)
    echo "=== FreeBSD: installing dependencies via pkg ==="
    sudo pkg install -y git gcc gmake python3 py311-pip py311-psutil py311-cryptography
    echo "[!] eBPF not available on FreeBSD — use dtrace/monitor.sh instead."
    ;;

  OpenBSD)
    echo "=== OpenBSD: installing dependencies via pkg_add ==="
    # OpenBSD uses doas instead of sudo
    PRIV="doas"
    command -v sudo >/dev/null 2>&1 && PRIV="sudo"
    $PRIV pkg_add git gcc gmake python3 py3-pip py3-cryptography
    echo "[!] eBPF not available on OpenBSD — use dtrace/monitor.sh instead."
    ;;

  NetBSD)
    echo "=== NetBSD: installing dependencies via pkgin ==="
    sudo pkgin install git gcc gmake python311 py311-pip py311-cryptography
    echo "[!] eBPF not available on NetBSD — use dtrace/monitor.sh instead."
    ;;

  *)
    echo "[!] Unsupported OS: $OS"
    echo "    Supported: Linux, FreeBSD, OpenBSD, NetBSD"
    exit 1
    ;;
esac

# ── Python venv ───────────────────────────────────────────────────────────────
PYTHON="python3"
command -v python3.11 >/dev/null 2>&1 && PYTHON="python3.11"

# On BSD, python3-bcc is not available, so don't use --system-site-packages
if [ "$OS" = "Linux" ]; then
    $PYTHON -m venv --system-site-packages .venv
else
    $PYTHON -m venv .venv
fi

. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ── Build native helpers ──────────────────────────────────────────────────────
# Use gmake on BSD (make is not GNU make)
MAKE_CMD="make"
case "$OS" in FreeBSD|OpenBSD|NetBSD) MAKE_CMD="gmake" ;; esac

$MAKE_CMD -C native

# ── Bootstrap config ──────────────────────────────────────────────────────────
if [ ! -f .env ]; then
    echo 'DISCORD_BOT_TOKEN=YOUR_TOKEN_HERE' > .env
    echo "[!] .env created — paste your bot token."
fi

if [ ! -f pysi-config.json ]; then
    python3 -c "from config.settings import Settings; Settings.load()"
fi

# ── DTrace permissions on BSD ─────────────────────────────────────────────────
if [ "$OS" = "FreeBSD" ] || [ "$OS" = "OpenBSD" ] || [ "$OS" = "NetBSD" ]; then
    chmod +x dtrace/monitor.sh
    echo "[!] DTrace monitor: sudo sh dtrace/monitor.sh"
fi

echo ""
echo "=== Done ==="
echo "  1. Edit .env             → DISCORD_BOT_TOKEN"
echo "  2. Edit pysi-config.json → add your Discord user ID to owner_ids"
echo "  3. source .venv/bin/activate"
echo "  4. python3 pysi_admin.py"
if [ "$OS" = "Linux" ]; then
    echo "  5. sudo .venv/bin/python3 ebpf/monitor.py   (optional, eBPF tracer)"
else
    echo "  5. sudo sh dtrace/monitor.sh                (optional, DTrace tracer)"
fi
