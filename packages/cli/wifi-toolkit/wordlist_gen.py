"""
WiFi Security Testing Toolkit — Wordlist Generator
Generates targeted wordlists based on known patterns, common passwords,
and SSID-based mutations.
"""

from __future__ import annotations

import itertools
import string
import re
from pathlib import Path
from typing import Iterator


class WordlistGenerator:
    """Generate password wordlists tuned for WiFi cracking."""

    # Top WiFi passwords observed in the wild
    COMMON_WIFI = [
        "password", "12345678", "1234567890", "qwerty123", "admin123",
        "letmein", "welcome", "changeme", "password123", "linkedin",
        "123456789", "0987654321", "123123123", "88888888", "00000000",
        "11111111", "22222222", "33333333", "44444444", "55555555",
        "66666666", "77777777", "99999999", "internet", "wireless",
        "mynetwork", "default", "guest123", "homewifi", "wifi123",
        "linksys", "netgear", "dlink", "tplink", "motorola",
        "iloveyou", "princess", "sunshine", "dragon", "monkey",
        "football", "baseball", "soccer", "hockey", "starwars",
        "pokemon", "minecraft", "fortnite", "batman", "superman",
    ]

    @classmethod
    def _digit_sequences(cls, length: int) -> Iterator[str]:
        """Generate all numeric sequences of given length."""
        fmt = f"{{:0{length}d}}"
        for i in range(10 ** length):
            yield fmt.format(i)

    @classmethod
    def _common_digits(cls) -> list[str]:
        """Common digit-only passwords."""
        patterns = []
        # Sequential: 12345678, 87654321
        for i in range(1, 10):
            seq = "".join(str((i + j) % 10) for j in range(8))
            patterns.append(seq)
            seq = "".join(str((i - j) % 10) for j in range(8))
            patterns.append(seq)
        # Repeated: 11111111
        for i in range(10):
            patterns.append(str(i) * 8)
            patterns.append(str(i) * 10)
        # Phone-style: 2345678901
        patterns.extend(["9876543210", "0123456789"])
        # Birth years
        for year in range(1950, 2026):
            patterns.append(str(year))
            patterns.append(str(year) * 2)
        return patterns

    @classmethod
    def _common_word_patterns(cls) -> list[str]:
        """Common word + number/symbol combinations."""
        words = [
            "password", "admin", "guest", "user", "wifi", "wireless",
            "home", "internet", "network", "router", "modem", "default",
            "secret", "private", "secure", "test", "demo",
        ]
        suffixes = ["123", "1", "12", "1234", "!", "@", "#", "2024", "2023",
                    "2025", "2026", "69", "007", "42", "01"]
        patterns = []
        for word in words:
            patterns.append(word)
            patterns.append(word.capitalize())
            patterns.append(word.upper())
            for suffix in suffixes:
                patterns.append(word + suffix)
                patterns.append(word.capitalize() + suffix)
        return patterns

    @classmethod
    def _ssid_mutations(cls, ssid: str) -> list[str]:
        """Generate passwords based on the SSID itself."""
        ssid = ssid.strip()
        if not ssid:
            return []

        mutations = [ssid, ssid.lower(), ssid.upper(),
                     ssid.replace(" ", ""), ssid.replace(" ", "_"),
                     ssid.replace(" ", "-")]

        # Remove common words from SSID
        words = re.split(r'[\s_-]+', ssid)
        for word in words:
            if len(word) >= 3:
                mutations.append(word.lower())
                mutations.append(word.capitalize())
                mutations.append(word.upper())

        # SSID + common suffixes
        suffixes = ["wifi", "net", "pass", "password", "123", "2024", "2025",
                    "1", "!", "@wifi", "_EXT", "_5G", "_2G"]
        clean_ssid = re.sub(r'\s+', '', ssid)
        for suffix in suffixes:
            mutations.append(clean_ssid + suffix)
            mutations.append(clean_ssid.lower() + suffix)

        # Common ISP SSID patterns
        isp_patterns = {
            "virgin": ["virginmedia", "virgin123", "changeme"],
            "bt": ["bthomehub", "btbroadband", "btinternet"],
            "sky": ["skybroadband", "skypassword"],
            "xfinity": ["xfinitywifi", "xfinity123"],
            "spectrum": ["spectrumwifi", "spectrum123"],
            "att": ["attwifi", "att123", "attwireless"],
            "vodafone": ["vodafonewifi", "vodafone123"],
            "t-mobile": ["tmobile", "tmobile123"],
            "ee": ["eebroadband", "eewifi"],
            "plusnet": ["plusnetwifi", "plusnet123"],
            "talktalk": ["talktalkwifi", "talktalk123"],
            "comcast": ["comcastwifi", "comcast123"],
            "cox": ["coxwifi", "cox123"],
            "centurylink": ["centurylink123", "centurylinkwifi"],
            "fios": ["verizonfios", "fios123"],
            "optimum": ["optimumwifi", "optimum123"],
            "frontier": ["frontierwifi", "frontier123"],
        }
        ssid_lower = ssid.lower()
        for key, patterns in isp_patterns.items():
            if key in ssid_lower:
                mutations.extend(patterns)

        return list(dict.fromkeys(mutations))  # Deduplicate preserving order

    @classmethod
    def _keyboard_patterns(cls) -> list[str]:
        """Common keyboard-walk patterns."""
        patterns = []
        rows = [
            "qwertyuiop", "asdfghjkl", "zxcvbnm",
            "qwertzuiop", "asdfghjklö", "yxcvbnm",
            "azertyuiop", "qsdfghjklm", "wxcvbn",
        ]
        for row in rows:
            for length in [8, 10, 12]:
                if length <= len(row):
                    patterns.append(row[:length])
                # Reverse
                patterns.append(row[:length][::-1])
            # Shifted: QWERTY -> 1qaz, 2wsx style
            for i in range(len(row) - 1):
                patterns.append(row[i:i + 2])

        # Diagonal walks
        diagonals = ["1qaz", "2wsx", "3edc", "4rfv", "5tgb", "6yhn",
                     "7ujm", "8ik,", "9ol.", "0p;/", "qaz", "wsx",
                     "edc", "rfv", "tgb", "yhn", "ujm", "ik,", "ol.", "p;/"]
        patterns.extend(diagonals)
        patterns.extend([d.upper() for d in diagonals])

        return patterns

    @classmethod
    def _phone_numbers(cls) -> list[str]:
        """Common patterns from phone numbers."""
        patterns = []
        # Local patterns: +1 area codes (US/Canada)
        for area in range(200, 999):
            # Skip invalid area codes
            if area % 100 == 11:  # x11 are service codes
                continue
            patterns.append(str(area) + "0000000")  # Area + zeros
            patterns.append(str(area) + "1234567")  # Area + sequential

        # UK-style: 07XXX XXXXXX
        for i in range(700, 800, 10):
            patterns.append(f"07{i}000000")
            patterns.append(f"07{i}123456")

        return patterns

    @classmethod
    def _date_patterns(cls) -> list[str]:
        """Common date-based passwords."""
        patterns = []
        months = ["jan", "feb", "mar", "apr", "may", "jun",
                  "jul", "aug", "sep", "oct", "nov", "dec"]
        for year in [str(y) for y in range(1990, 2027)]:
            patterns.append(year)
            for month in months:
                patterns.append(month + year)
                patterns.append(month.capitalize() + year)
                patterns.append(month.upper() + year)
        return patterns

    @classmethod
    def generate(cls, ssid: str = "", output: str | Path | None = None,
                 size: str = "medium") -> list[str]:
        """
        Generate a targeted wordlist.

        Sizes:
        - small:  ~10K  entries (fast)
        - medium: ~100K  entries (thorough)
        - large:  ~1M   entries (exhaustive)
        """
        wordlist: list[str] = []

        # Base common passwords
        wordlist.extend(cls.COMMON_WIFI)

        # Common word patterns
        wordlist.extend(cls._common_word_patterns())

        # Digit patterns
        wordlist.extend(cls._common_digits())

        # Keyboard patterns
        wordlist.extend(cls._keyboard_patterns())

        # SSID mutations
        if ssid:
            wordlist.extend(cls._ssid_mutations(ssid))

        # Date patterns
        wordlist.extend(cls._date_patterns())

        if size in ("medium", "large"):
            # 8-digit numbers
            wordlist.extend(cls._digit_sequences(8))

            # Phone numbers
            wordlist.extend(cls._phone_numbers())

            # Common words + 2-digit suffix
            for i in range(100):
                suffix = f"{i:02d}"
                for word in ["password", "admin", "wifi", "guest", "test"]:
                    wordlist.append(word + suffix)
                    wordlist.append(word.capitalize() + suffix)

        if size == "large":
            # All combinations of 2-char lower + 6 digits
            for a in string.ascii_lowercase:
                for b in string.ascii_lowercase:
                    wordlist.append(f"{a}{b}123456")
                    wordlist.append(f"{a}{b}654321")

            # All 10-digit numbers (phone numbers)
            for i in range(2000000000, 2001000000):
                wordlist.append(str(i))

            # l33t speak variations of common words
            leet_map = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}
            base_words = ["password", "admin", "welcome", "letmein", "sunshine",
                          "princess", "dragon", "monkey", "football", "superman"]
            for word in base_words:
                # Apply leet
                leet = "".join(leet_map.get(c, c) for c in word.lower())
                wordlist.append(leet)
                wordlist.append(leet.capitalize())

        # Deduplicate
        wordlist = list(dict.fromkeys(wordlist))

        # Filter by length (WPA requires 8-63 chars)
        wordlist = [w for w in wordlist if 8 <= len(w) <= 63]

        # Remove non-ASCII
        wordlist = [w for w in wordlist if all(ord(c) < 128 for c in w)]

        if output:
            out_path = Path(output)
            out_path.write_text("\n".join(wordlist))
            print(f"[*] Generated {len(wordlist):,} passwords → {output}")
            print(f"[*] Use with: hashcat -m 22000 handshake.hc22000 {output}")

        return wordlist


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WiFi Wordlist Generator")
    parser.add_argument("-s", "--ssid", default="",
                        help="Target SSID for targeted mutations")
    parser.add_argument("-o", "--output", default="wordlist.txt",
                        help="Output file path")
    parser.add_argument("--size", choices=["small", "medium", "large"],
                        default="medium",
                        help="Wordlist size (small=10K, medium=100K, large=1M)")
    args = parser.parse_args()

    WordlistGenerator.generate(ssid=args.ssid, output=args.output,
                                size=args.size)
