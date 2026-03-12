"""
cocotb testbench for project.v — 4-round encrypt/decrypt core
Run with:
    make MODULE=test_project TOPLEVEL=project TOPLEVEL_LANG=verilog
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles
import random

# ──────────────────────────────────────────────
# Python mirror of the Verilog functions
# ──────────────────────────────────────────────
MASK = 0xFF

R1 = 0b10001001   # 0x89
R2 = 0b11110111   # 0xF7
R3 = 0b11110001   # 0xF1
R4 = 0b01110101   # 0x75


def left_rotate(x: int) -> int:
    """Rotate left by 3 bits (8-bit)."""
    x &= MASK
    return ((x << 3) | (x >> 5)) & MASK


def right_rotate(x: int) -> int:
    """Rotate right by 3 bits (8-bit)."""
    x &= MASK
    return ((x >> 3) | (x << 5)) & MASK


def encrypt_round(x: int, key: int, r: int) -> int:
    return ((left_rotate(x ^ key) + key) ^ r) & MASK


def decrypt_round(x: int, key: int, r: int) -> int:
    return (right_rotate((x ^ r) - key) ^ key) & MASK


def sw_encrypt(text: int, key: int) -> int:
    key &= 0x7F          # MSB hard-coded to 0, matching the RTL
    t = encrypt_round(text, key, R1)
    t = encrypt_round(t,    key, R2)
    t = encrypt_round(t,    key, R3)
    t = encrypt_round(t,    key, R4)
    return t


def sw_decrypt(text: int, key: int) -> int:
    key &= 0x7F
    t = decrypt_round(text, key, R4)
    t = decrypt_round(t,    key, R3)
    t = decrypt_round(t,    key, R2)
    t = decrypt_round(t,    key, R1)
    return t


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
async def reset(dut):
    """Assert active-low reset for 5 cycles."""
    dut.rst_n.value  = 0
    dut.ui_in.value  = 0
    dut.uio_in.value = 0
    dut.ena.value    = 1
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value  = 1
    await RisingEdge(dut.clk)


async def apply_and_sample(dut, text: int, key_raw: int, mode: int) -> int:
    """
    Drive inputs, wait one clock for the output register to capture,
    then return the sampled output.

    uio_in[7]   = mode
    uio_in[6:0] = key (lower 7 bits)
    """
    dut.ui_in.value  = text & MASK
    dut.uio_in.value = ((mode & 1) << 7) | (key_raw & 0x7F)
    await RisingEdge(dut.clk)   # combinational logic settles
    await RisingEdge(dut.clk)   # output register captures
    return int(dut.uo_out.value)


# ──────────────────────────────────────────────
# Test 1 — Reset check
# ──────────────────────────────────────────────
@cocotb.test()
async def test_reset(dut):
    """Output should be 0x00 immediately after reset."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    assert int(dut.uo_out.value) == 0x00, (
        f"Expected 0x00 after reset, got {int(dut.uo_out.value):#04x}"
    )
    dut._log.info("PASS — reset drives uo_out to 0x00")


# ──────────────────────────────────────────────
# Test 2 — Known-value encrypt
# ──────────────────────────────────────────────
@cocotb.test()
async def test_known_encrypt(dut):
    """Encrypt a handful of known (text, key) pairs and compare to SW model."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    vectors = [
        (0x00, 0x00),
        (0xFF, 0x7F),
        (0xAB, 0x55),
        (0x42, 0x13),
        (0x01, 0x01),
    ]

    for text, key in vectors:
        expected = sw_encrypt(text, key)
        got      = await apply_and_sample(dut, text, key, mode=1)
        assert got == expected, (
            f"ENCRYPT text={text:#04x} key={key:#04x} "
            f"expected={expected:#04x} got={got:#04x}"
        )
        dut._log.info(
            f"PASS — encrypt(0x{text:02X}, 0x{key:02X}) = 0x{got:02X}"
        )


# ──────────────────────────────────────────────
# Test 3 — Known-value decrypt
# ──────────────────────────────────────────────
@cocotb.test()
async def test_known_decrypt(dut):
    """Decrypt a handful of known (ciphertext, key) pairs and compare to SW model."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    vectors = [
        (0x00, 0x00),
        (0xFF, 0x7F),
        (0xAB, 0x55),
        (0x42, 0x13),
        (0x01, 0x01),
    ]

    for text, key in vectors:
        # Build the ciphertext first via the SW model
        ciphertext = sw_encrypt(text, key)
        expected   = sw_decrypt(ciphertext, key)   # should equal text
        got        = await apply_and_sample(dut, ciphertext, key, mode=0)

        assert got == expected, (
            f"DECRYPT cipher={ciphertext:#04x} key={key:#04x} "
            f"expected={expected:#04x} got={got:#04x}"
        )
        dut._log.info(
            f"PASS — decrypt(0x{ciphertext:02X}, 0x{key:02X}) = 0x{got:02X}"
        )


# ──────────────────────────────────────────────
# Test 4 — Round-trip: encrypt then decrypt
# ──────────────────────────────────────────────
@cocotb.test()
async def test_roundtrip(dut):
    """Encrypt plaintext, then decrypt the result — must recover the original."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    vectors = [
        (0x00, 0x00),
        (0xFF, 0x7F),
        (0xAB, 0x55),
        (0x42, 0x13),
        (0xDE, 0x1A),
        (0xBE, 0x55),
        (0xCA, 0x7F),
        (0x80, 0x40),
    ]

    for plaintext, key in vectors:
        ciphertext = await apply_and_sample(dut, plaintext, key, mode=1)
        recovered  = await apply_and_sample(dut, ciphertext, key, mode=0)

        assert recovered == plaintext, (
            f"ROUNDTRIP FAIL plain={plaintext:#04x} key={key:#04x} "
            f"cipher={ciphertext:#04x} recovered={recovered:#04x}"
        )
        dut._log.info(
            f"PASS — roundtrip 0x{plaintext:02X} -> "
            f"0x{ciphertext:02X} -> 0x{recovered:02X}  (key=0x{key:02X})"
        )


# ──────────────────────────────────────────────
# Test 5 — Random round-trip (stress)
# ──────────────────────────────────────────────
@cocotb.test()
async def test_random_roundtrip(dut):
    """100 random (plaintext, key) round-trips."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    rng = random.Random(42)
    failures = 0

    for i in range(100):
        plaintext = rng.randint(0, 0xFF)
        key       = rng.randint(0, 0x7F)

        ciphertext = await apply_and_sample(dut, plaintext, key, mode=1)
        recovered  = await apply_and_sample(dut, ciphertext, key, mode=0)

        if recovered != plaintext:
            dut._log.error(
                f"[{i}] FAIL plain={plaintext:#04x} key={key:#04x} "
                f"cipher={ciphertext:#04x} recovered={recovered:#04x}"
            )
            failures += 1

    assert failures == 0, f"{failures}/100 random round-trips failed"
    dut._log.info("PASS — 100 random round-trips all passed")


# ──────────────────────────────────────────────
# Test 6 — RTL output matches SW model (encrypt)
# ──────────────────────────────────────────────
@cocotb.test()
async def test_sw_model_encrypt(dut):
    """RTL encrypt output must exactly match the Python SW model for all keys on a fixed plaintext."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    plaintext = 0xA5
    failures  = 0

    for key in range(0x80):          # 0x00 .. 0x7F (7-bit key space)
        expected = sw_encrypt(plaintext, key)
        got      = await apply_and_sample(dut, plaintext, key, mode=1)
        if got != expected:
            dut._log.error(
                f"SW-model mismatch: key={key:#04x} "
                f"expected={expected:#04x} got={got:#04x}"
            )
            failures += 1

    assert failures == 0, (
        f"{failures} mismatches vs SW model over full 7-bit key space"
    )
    dut._log.info("PASS — RTL matches SW model over full 7-bit key space (encrypt)")


# ──────────────────────────────────────────────
# Test 7 — Mode switch mid-stream
# ──────────────────────────────────────────────
@cocotb.test()
async def test_mode_switch(dut):
    """Switch between encrypt and decrypt on consecutive cycles — no glitches."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset(dut)

    pairs = [(0x12, 0x34), (0xAB, 0x7F), (0xFF, 0x00), (0x55, 0x2A)]

    for plaintext, key in pairs:
        enc = await apply_and_sample(dut, plaintext, key, mode=1)
        dec = await apply_and_sample(dut, enc,       key, mode=0)

        assert dec == plaintext, (
            f"Mode-switch FAIL plain={plaintext:#04x} "
            f"enc={enc:#04x} dec={dec:#04x}"
        )
    dut._log.info("PASS — mode switching encrypt<->decrypt produces correct outputs")
