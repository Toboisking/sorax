#!/usr/bin/env bash
# WiFi Toolkit — Dependency Installer
# Installs all system packages and Python dependencies needed.

set -e

echo "============================================"
echo "  WiFi Toolkit Dependency Installer"
echo "============================================"

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
elif [ "$(uname)" = "Darwin" ]; then
    OS="macos"
else
    echo "[!] Unsupported OS. Install dependencies manually."
    exit 1
fi

echo "[*] Detected OS: $OS"

# System dependencies
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ] || [ "$OS" = "kali" ] || [ "$OS" = "parrot" ]; then
    echo "[*] Installing system packages (Debian/Ubuntu/Kali)..."
    sudo apt update
    sudo apt install -y \
        aircrack-ng \
        reaver \
        bully \
        hostapd \
        dnsmasq \
        iptables \
        net-tools \
        wireless-tools \
        python3 \
        python3-pip \
        hashcat \
        hcxtools \
        hcxdumptool \
        macchanger 2>/dev/null || true

    # Enable IP forwarding
    sudo sysctl -w net.ipv4.ip_forward=1

elif [ "$OS" = "arch" ] || [ "$OS" = "manjaro" ]; then
    echo "[*] Installing system packages (Arch)..."
    sudo pacman -S --noconfirm \
        aircrack-ng \
        reaver \
        bully \
        hostapd \
        dnsmasq \
        iptables \
        python \
        python-pip \
        hashcat \
        hcxtools \
        macchanger 2>/dev/null || true

elif [ "$OS" = "fedora" ] || [ "$OS" = "rhel" ] || [ "$OS" = "centos" ]; then
    echo "[*] Installing system packages (Fedora/RHEL)..."
    sudo dnf install -y \
        aircrack-ng \
        reaver \
        hostapd \
        dnsmasq \
        iptables \
        python3 \
        python3-pip \
        hashcat \
        hcxtools

elif [ "$OS" = "macos" ]; then
    echo "[*] Installing via Homebrew (macOS)..."
    echo "[!] macOS has limited monitor mode support. Use Linux for full functionality."
    brew install aircrack-ng hashcat python 2>/dev/null || true
fi

# Python dependencies
echo "[*] Installing Python packages..."
cd "$(dirname "$0")"
pip3 install -r requirements.txt

echo ""
echo "============================================"
echo "  Installation Complete!"
echo "============================================"
echo ""
echo "  Quick start:"
echo "    sudo python3 nexus.py scan"
echo "    sudo python3 nexus.py full -w wordlist.txt"
echo ""
echo "  Generate a wordlist:"
echo "    python3 wordlist_gen.py -s \"MyWiFi\" --size medium"
echo ""
echo "  For hashcat GPU acceleration:"
echo "    hashcat -m 22000 capture.hc22000 wordlist.txt -O"
echo ""
