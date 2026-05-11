# Vanity Ethereum Address Generator

A fast, lightweight tool for generating vanity or pattern-based Ethereum-compatible addresses (`0x` prefixed) by brute-forcing cryptographic keypairs.

This script continuously generates wallet addresses until it finds one matching a user-defined pattern such as leading zeros or custom prefixes.

---

## Why Generate a Vanity Address?

There are a few reasons you might want a specific address pattern:

**Aesthetics and identity** — A recognisable prefix like `0xdead...`, `0xcafe...`, or your initials makes an address easier to spot in transaction lists and easier to verify at a glance.

**Gas optimisation (rumoured)** — A popular claim is that addresses with many leading zeros (e.g. `0x0000...`) cost less gas when used as a recipient, because the EVM charges less for zero bytes in calldata (1 gas vs 16 gas per byte under EIP-2028 / EIP-3860). The address itself is stored as 20 bytes, and more leading zero bytes in the address means cheaper `CALL` transactions to that address. This is real — but the savings are modest (a few hundred gas per call) and only matter at high call volume.

**Smart contract deployment** — Tools like `CREATE2` let you pre-compute a contract address. A vanity address for a contract can signal intent (e.g. a protocol's main contract starting with `0x1337...`) and the leading-zero gas benefit applies here too.

**Fun / proof of work** — Generating a pattern is a harmless demonstration that you understand how Ethereum keypairs work.

---

## Features

- Generate Ethereum-compatible addresses (`0x` format)
- Custom vanity patterns (prefix-based matching)
- Support for leading zero addresses (e.g., `0x0000...`)
- Works across all EVM-compatible chains (Ethereum, Polygon, BSC, Arbitrum, etc.)
- Configurable difficulty (pattern length vs. search time)
- Multi-threading / parallel execution for faster generation

---

## How It Works

The tool repeatedly generates random private keys and derives the corresponding Ethereum address. Each generated address is checked against the target pattern until a match is found.

Because Ethereum addresses are derived from cryptographic hash functions, finding a specific pattern is probabilistic and requires brute-force search.

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Usage

```bash
python generate.py --pattern 0000
```

Example output:

```
Address:     0x0000af3bc9d2e4...
Private key: 0xabcdef1234...
```

---

## Parameters

| Flag | Description | Default |
|------|-------------|---------|
| `--pattern` | Desired prefix pattern (e.g. `0000`, `dead`, `cafe`) | required |
| `--threads` | Number of parallel workers | CPU count |
| `--limit` | Maximum attempts per thread before stopping (`0` = unlimited) | `0` |

---

## Example

Generate an address starting with four zeros:

```bash
python generate.py --pattern 0000
```

---

## Performance Notes

- Each additional character in the pattern increases difficulty exponentially
- Short patterns (2–5 characters) are typically fast to find
- Longer patterns may require multi-threading or extended search time
- Vanity search is CPU-intensive and time-dependent

---

## Disclaimer

This tool is intended for educational and experimental use only. It does not weaken cryptographic security, but it may require significant computational resources depending on pattern complexity.

Use responsibly and securely handle any generated private keys.
