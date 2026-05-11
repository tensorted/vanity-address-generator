import argparse
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import coincurve
import sha3


def derive_address(private_key_bytes: bytes) -> tuple[str, str]:
    pub = coincurve.PublicKey.from_valid_secret(private_key_bytes)
    pub_bytes = pub.format(compressed=False)[1:]  # strip 04 prefix → 64 bytes
    k = sha3.keccak_256()
    k.update(pub_bytes)
    address = "0x" + k.hexdigest()[-40:]
    return "0x" + private_key_bytes.hex(), address


def matches_pattern(address: str, pattern: str) -> bool:
    return address[2 : 2 + len(pattern)].lower() == pattern.lower()


def worker(
    pattern: str,
    found: threading.Event,
    result: list,
    result_lock: threading.Lock,
    limit: int,
) -> None:
    attempts = 0
    while not found.is_set():
        if limit > 0 and attempts >= limit:
            break
        private_key = os.urandom(32)
        priv_hex, address = derive_address(private_key)
        attempts += 1
        if attempts % 100_000 == 0:
            print(f"\r[~] ~{attempts:,} attempts...", file=sys.stderr, end="", flush=True)
        if matches_pattern(address, pattern):
            with result_lock:
                if not found.is_set():
                    found.set()
                    result.append((priv_hex, address, attempts))
            break


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a vanity Ethereum address")
    parser.add_argument("--pattern", required=True, help="Hex prefix to match (after 0x)")
    parser.add_argument(
        "--threads",
        type=int,
        default=os.cpu_count() or 1,
        help="Number of worker threads (default: CPU count)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max attempts per thread before stopping (0 = unlimited)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = parse_args(argv)
    pattern = args.pattern.lower()

    if pattern.startswith("0x"):  # pattern is already lowercased, so this catches 0X too
        print("Error: --pattern should not include '0x' prefix (e.g. use 'dead' not '0xdead')", file=sys.stderr)
        sys.exit(1)
    if len(pattern) == 0:
        print("Error: --pattern cannot be empty", file=sys.stderr)
        sys.exit(1)

    try:
        int(pattern, 16)
    except ValueError:
        print(f"Error: --pattern must be a hex string, got: {pattern!r}", file=sys.stderr)
        sys.exit(1)
    if len(pattern) > 40:
        print("Error: --pattern cannot be longer than 40 characters", file=sys.stderr)
        sys.exit(1)

    threads = max(1, args.threads)
    limit = max(0, args.limit)
    found = threading.Event()
    result = []
    result_lock = threading.Lock()

    print(
        f"[*] Searching for 0x{pattern}... using {threads} thread(s)",
        file=sys.stderr,
    )

    try:
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [
                executor.submit(worker, pattern, found, result, result_lock, limit)
                for _ in range(threads)
            ]
            for _ in as_completed(futures):
                if found.is_set():
                    break
    except KeyboardInterrupt:
        found.set()
        print("\n[-] Interrupted.", file=sys.stderr)
        sys.exit(0)

    if result:
        priv_hex, address, attempts = result[0]
        print(f"\n[+] Found after ~{attempts * threads:,} attempts\n", file=sys.stderr)
        print(f"Address:     {address}")
        print(f"Private key: {priv_hex}")
    else:
        print("\n[-] No match found.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
