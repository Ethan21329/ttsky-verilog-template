# Makefile for cocotb — works with Icarus Verilog (default) or Verilator
# Usage:
#   make                        (Icarus)
#   make SIM=verilator          (Verilator)

SIM        ?= icarus
TOPLEVEL_LANG ?= verilog
VERILOG_SOURCES = $(PWD)/../src/encrypt.v
WAVES = 1

TOPLEVEL = tt_um_encrypt
MODULE   = test

include $(shell cocotb-config --makefiles)/Makefile.sim

clean::
	rm -rf __pycache__
	rm -rf sim_build
	