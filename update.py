#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-update US-only Cloudflare preferred IP list.
Fetches several public CF preferred-IP sources, keeps only US entries,
deduplicates, and writes:
  - best-cf-us.txt        (all US IPs found)
  - best-cf-us-top20.txt  (first 20)
Format per line (edgetunnel / cfnew compatible):
  IP:port#US 🇺🇸
If fewer than 5 IPs are found, the old files are kept (no overwrite),
so a temporary upstream outage does not empty your node list.
"""
import ipaddress
import re
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

# Cloudflare IPv4 ranges (fallback if live fetch fails). Checked 2026-11-26
# from https://www.cloudflare.com/ips-v4/
CF_RANGES_FALLBACK = [
    "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
    "141.101.64.0/18", "108.162.192.0/18", "190.93.240.0/20", "188.114.96.0/20",
    "197.234.240.0/22", "198.41.128.0/17", "162.158.0.0/15", "104.16.0.0/13",
    "104.24.0.0/14", "172.64.0.0/13", "131.0.72.0/22",
]


def load_cf_networks():
    try:
        text = fetch("https://www.cloudflare.com/ips-v4/")
        nets = [ipaddress.ip_network(x.strip()) for x in text.splitlines() if x.strip()]
        if nets:
            return nets
    except Exception as e:
        print(f"WARN: CF ranges fetch failed, using fallback: {e}", file=sys.stderr)
    return [ipaddress.ip_network(x) for x in CF_RANGES_FALLBACK]


def is_cf_ip(ip, networks):
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(addr in n for n in networks)

# Public sources, checked 2026-11-26. Add/remove freely.
SOURCES = [
    # LancelotRar scanned lists (filter #US only) - largest pool
    ("https://raw.githubusercontent.com/LancelotRar/best-cf-ips/main/best-cf-ip-scanned-top400.txt", "filter_us"),
    # US-specific lists mirrored at bestcf.pages.dev (all entries are US)
    ("https://bestcf.pages.dev/tiancheng/us.txt", "all_us"),
    ("https://bestcf.pages.dev/tiancheng2/us.txt", "all_us"),
    ("https://bestcf.pages.dev/gslege/US.txt", "all_us"),
]

IP_PORT_RE = re.compile(r"^(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})#?(.*)$")
ALLOWED_PORTS = {"443", "8443", "2053", "2083", "2087", "2096"}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "my-cf-us-auto/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def parse(text, mode, networks):
    out = []
    skipped_non_cf = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = IP_PORT_RE.match(line)
        if not m:
            continue
        ip, port, remark = m.group(1), m.group(2), m.group(3) or ""
        if port not in ALLOWED_PORTS:
            continue
        if mode == "filter_us" and "US" not in remark.upper():
            continue
        # Only keep real Cloudflare edge IPs. Some public US lists mix in
        # ProxyIP / VPS addresses, which do not work as edgetunnel preferred IPs.
        if not is_cf_ip(ip, networks):
            skipped_non_cf += 1
            continue
        out.append(f"{ip}:{port}#US 🇺🇸")
    if skipped_non_cf:
        print(f"  skipped {skipped_non_cf} non-Cloudflare IPs")
    return out


def main():
    networks = load_cf_networks()
    seen = []
    seen_set = set()
    for url, mode in SOURCES:
        try:
            text = fetch(url)
            items = parse(text, mode, networks)
            print(f"{url} -> {len(items)} US entries")
            for it in items:
                key = it.split("#")[0]
                if key not in seen_set:
                    seen_set.add(key)
                    seen.append(it)
        except Exception as e:
            print(f"WARN: failed {url}: {e}", file=sys.stderr)

    print(f"Total unique US entries: {len(seen)}")
    if len(seen) < 5:
        print("Too few entries (<5), keeping old files. Exiting without overwrite.")
        return 0

    now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")
    header = f"# {len(seen)} US cf ips aggregated at {now} (Asia/Shanghai)\n"
    with open("best-cf-us.txt", "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(seen) + "\n")

    top20 = seen[:20]
    header20 = f"# {len(top20)} US cf ips aggregated at {now} (Asia/Shanghai)\n"
    with open("best-cf-us-top20.txt", "w", encoding="utf-8") as f:
        f.write(header20)
        f.write("\n".join(top20) + "\n")

    print("Wrote best-cf-us.txt and best-cf-us-top20.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
