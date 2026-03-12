# Makefile for cocotb — works with Icarus Verilog (default) or Verilator
# Usage:
#   make                        (Icarus)
#   make SIM=verilator          (Verilator)

SIM        ?= icarus
TOPLEVEL_LANG ?= verilog
VERILOG_SOURCES = $(PWD)/../src/project.v
WAVES = 1

TOPLEVEL = project
MODULE   = test

include $(shell cocotb-config --makefiles)/Makefile.sim

clean::
	rm -rf __pycache__
	rm -rf sim_build
	