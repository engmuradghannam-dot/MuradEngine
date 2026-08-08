# Bitcoin Puzzle Solver CUDA Makefile

CUDA_PATH ?= /usr/local/cuda
NVCC = $(CUDA_PATH)/bin/nvcc

# Architecture flags for RTX 4070 (Compute Capability 8.9)
ARCH_FLAGS = -gencode arch=compute_89,code=sm_89

# Compiler flags
NVCC_FLAGS = -O3 $(ARCH_FLAGS) -Xcompiler -fPIC
NVCC_FLAGS += --use_fast_math
NVCC_FLAGS += -lineinfo

# For shared library
SHARED_FLAGS = -shared -o puzzle_solver_cuda.so

# Source files
SRC = puzzle_solver_cuda.cu

# Targets
all: shared

shared: $(SRC)
	$(NVCC) $(NVCC_FLAGS) $(SHARED_FLAGS) $(SRC)
	@echo "✅ Shared library compiled: puzzle_solver_cuda.so"

static: $(SRC)
	$(NVCC) $(NVCC_FLAGS) -lib -o puzzle_solver_cuda.a $(SRC)
	@echo "✅ Static library compiled: puzzle_solver_cuda.a"

clean:
	rm -f puzzle_solver_cuda.so puzzle_solver_cuda.a *.o
	@echo "🗑️ Cleaned build files"

info:
	@echo "CUDA Path: $(CUDA_PATH)"
	@echo "NVCC: $(NVCC)"
	@nvcc --version

# Install PyCUDA
install-pycuda:
	pip install pycuda

# Run solver
run: shared
	python puzzle_solver_v33.py
