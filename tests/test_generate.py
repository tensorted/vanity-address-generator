import os
import pytest
import threading
from generate import derive_address, matches_pattern, worker, parse_args, main
import io
from contextlib import redirect_stdout


HARDHAT_PRIVATE_KEY = bytes.fromhex(
    "ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
)
HARDHAT_ADDRESS = "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266"


def test_derive_address_format():
    priv_hex, address = derive_address(bytes(31) + b'\x01')
    assert priv_hex.startswith("0x")
    assert len(priv_hex) == 66
    assert address.startswith("0x")
    assert len(address) == 42


def test_derive_address_known_vector():
    priv_hex, address = derive_address(HARDHAT_PRIVATE_KEY)
    assert priv_hex == "0x" + HARDHAT_PRIVATE_KEY.hex()
    assert address == HARDHAT_ADDRESS


def test_matches_pattern_prefix_match():
    assert matches_pattern("0xdeadbeef1234", "dead") is True


def test_matches_pattern_no_match():
    assert matches_pattern("0xdeadbeef1234", "cafe") is False


def test_matches_pattern_case_insensitive():
    assert matches_pattern("0xDEADBEEF1234", "dead") is True
    assert matches_pattern("0xdeadbeef1234", "DEAD") is True


def test_matches_pattern_empty_pattern():
    assert matches_pattern("0xdeadbeef1234", "") is True


def test_matches_pattern_full_address():
    assert matches_pattern("0xdeadbeef1234567890abcdef1234567890abcdef", "deadbeef1234567890abcdef1234567890abcdef") is True


def test_worker_finds_trivial_pattern():
    found = threading.Event()
    result = []
    result_lock = threading.Lock()
    worker("", found, result, result_lock, limit=0)
    assert found.is_set()
    assert len(result) == 1
    priv_hex, address, attempts = result[0]
    assert priv_hex.startswith("0x") and len(priv_hex) == 66
    assert address.startswith("0x") and len(address) == 42
    assert attempts >= 1


def test_worker_exits_when_found_already_set():
    found = threading.Event()
    found.set()
    result = []
    result_lock = threading.Lock()
    worker("0" * 40, found, result, result_lock, limit=0)
    assert result == []


def test_worker_respects_limit():
    found = threading.Event()
    result = []
    result_lock = threading.Lock()
    # 40-char all-zeros pattern: ~1/16^40 probability — won't match in 1 attempt
    worker("0" * 40, found, result, result_lock, limit=1)
    assert not found.is_set()
    assert result == []


def test_parse_args_defaults():
    args = parse_args(["--pattern", "dead"])
    assert args.pattern == "dead"
    assert args.threads == (os.cpu_count() or 1)
    assert args.limit == 0


def test_parse_args_custom_values():
    args = parse_args(["--pattern", "cafe", "--threads", "4", "--limit", "1000000"])
    assert args.pattern == "cafe"
    assert args.threads == 4
    assert args.limit == 1_000_000


def test_main_rejects_non_hex_pattern():
    with pytest.raises(SystemExit) as exc:
        main(["--pattern", "xyz!"])
    assert exc.value.code == 1


def test_main_rejects_overlong_pattern():
    with pytest.raises(SystemExit) as exc:
        main(["--pattern", "a" * 41])
    assert exc.value.code == 1


def test_main_finds_match_and_prints_result(capsys):
    # empty pattern matches everything — should find a result instantly
    main(["--pattern", "0", "--threads", "1", "--limit", "100000"])
    captured = capsys.readouterr()
    assert "Address:" in captured.out
    assert "Private key:" in captured.out
    assert captured.out.count("0x") == 2


def test_main_rejects_0x_prefix_in_pattern():
    with pytest.raises(SystemExit) as exc:
        main(["--pattern", "0xdead"])
    assert exc.value.code == 1


def test_main_rejects_empty_pattern():
    with pytest.raises(SystemExit) as exc:
        main(["--pattern", ""])
    assert exc.value.code == 1
