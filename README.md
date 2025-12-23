# xv6-riscv Automated Testing Framework

A comprehensive automated testing framework for the xv6-riscv operating system, built with Python, pytest, and pexpect.

**Project Statistics:**
- 82 test cases across 4 modules
- 98.8% pass rate
- Automated testing with one-click execution

**Team:**
- 314553037 Chen Wei-Yu (陳威宇)
- 314551135 Peng Yi-Qun (彭逸群)

**Course:** Software Testing - Fall 2024

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [Test Results](#test-results)
- [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### Required Software

| Software | Version | Check Command |
|----------|---------|---------------|
| Python | 3.8+ | `python3 --version` |
| QEMU | Latest | `qemu-system-riscv64 --version` |
| RISC-V GCC | Latest | `riscv64-linux-gnu-gcc --version` |
| Git | Any | `git --version` |

### Operating System

- **Linux**: Ubuntu 20.04 or newer (recommended)
- **WSL 2**: Windows Subsystem for Linux version 2
- **macOS**: With Homebrew (limited testing)

---

## 🚀 Installation

### Step 1: Install System Dependencies

**For Ubuntu/Debian/WSL:**

```bash
# Update package list
sudo apt-get update

# Install all required tools in one command
sudo apt-get install -y \
    git \
    build-essential \
    gdb-multiarch \
    qemu-system-misc \
    gcc-riscv64-linux-gnu \
    binutils-riscv64-linux-gnu \
    python3 \
    python3-pip \
    python3-venv
```

**Verify installation:**
```bash
python3 --version        # Should show 3.8 or higher
qemu-system-riscv64 --version
riscv64-linux-gnu-gcc --version
```

### Step 2: Clone Repositories

```bash
# Create project directory
mkdir -p ~/software-testing-project
cd ~/software-testing-project

# Clone this test framework
git clone https://github.com/YOUR_USERNAME/xv6-test-framework.git

# Clone xv6-riscv OS
git clone https://github.com/mit-pdos/xv6-riscv.git
```

**Directory structure:**
```
~/software-testing-project/
├── xv6-test-framework/    # This repository
└── xv6-riscv/             # xv6 operating system
```

### Step 3: Build xv6

```bash
# Navigate to xv6 directory
cd ~/software-testing-project/xv6-riscv

# Compile xv6
make

# Test xv6 manually (optional)
make qemu
# You should see xv6 boot and show a shell prompt $
# Press Ctrl-A, then press X to exit
```

**If compilation fails:**
```bash
# Fix toolchain prefix in Makefile
sed -i 's/riscv64-unknown-elf-/riscv64-linux-gnu-/g' Makefile
make clean
make
```

### Step 4: Setup Python Environment

```bash
# Navigate to test framework
cd ~/software-testing-project/xv6-test-framework

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
# You should see (venv) at the start of your prompt

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Verify Installation

```bash
# Make sure you're in the test framework directory with venv activated
cd ~/software-testing-project/xv6-test-framework
source venv/bin/activate

# Run verification script
python verify_setup.py
```

**Expected output:**
```
=== xv6 測試框架環境檢查 ===

✓ Git 已安裝
✓ QEMU RISC-V 已安裝
✓ RISC-V GCC 已安裝
✓ Python 3.x
✓ pytest 已安裝
✓ pexpect 已安裝
✓ xv6 已編譯

✅ 環境設置完成！
```

---

## ▶️ How to Run

### Quick Start (Recommended)

```bash
# 1. Navigate to project directory
cd ~/software-testing-project/xv6-test-framework

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run all fast tests (~3 minutes)
pytest tests/ -v -m "not slow"
```

### Run All Tests

```bash
# Run complete test suite including slow tests (~5 minutes)
pytest tests/ -v
```

### Run Specific Test Modules

```bash
# Basic functionality tests (12 tests, ~45 seconds)
pytest tests/test_basic.py -v

# Filesystem tests (22 tests, ~45 seconds)
pytest tests/test_filesystem.py -v

# Process management tests (17 tests, ~2 minutes)
pytest tests/test_process.py -v

# Fuzzing tests (31 tests, ~2 minutes)
pytest tests/test_fuzzing.py -v
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/test_filesystem.py::TestFileCreation -v

# Run a single test function
pytest tests/test_basic.py::TestBasicCommands::test_echo_command -v
```

### Generate Test Reports

```bash
# Generate HTML report
pytest tests/ -v --html=reports/test_report.html --self-contained-html

# Open the report (WSL)
explorer.exe reports/test_report.html

# Open the report (Linux)
firefox reports/test_report.html
```

### Run with Live Output (Debug Mode)

```bash
# Show real-time output (useful for debugging)
pytest tests/ -v -s
```

### Run Only Failed Tests

```bash
# Re-run only the tests that failed last time
pytest tests/ --lf -v
```

---

## 📊 Test Results

### Expected Output

When all tests pass, you should see:

```
========================= test session starts ==========================
collected 82 items

tests/test_basic.py::TestBasicCommands::test_echo_command PASSED  [  1%]
tests/test_basic.py::TestBasicCommands::test_ls_command PASSED    [  2%]
...
tests/test_fuzzing.py::TestRandomFuzzing::test_random_valid_operations PASSED [100%]

==================== 81 passed, 1 skipped in 240.00s ===================
```

### Test Summary

| Test Module | Tests | Expected Result | Time |
|------------|-------|----------------|------|
| test_basic.py | 12 | 12 passed | ~45s |
| test_filesystem.py | 22 | 22 passed | ~45s |
| test_process.py | 17 | 17 passed | ~2m |
| test_fuzzing.py | 31 | 30 passed, 1 skipped | ~2m |
| **TOTAL** | **82** | **81 passed, 1 skipped** | **~4-5m** |

*Note: 1 test (usertests) is skipped due to long execution time (>5 minutes)*

---

## 🐛 Troubleshooting

### Issue 1: "Failed to get write lock" Error

**Symptom:**
```
qemu-system-riscv64: Failed to get "write" lock
Is another process using the image [fs.img]?
```

**Cause:** Previous QEMU process didn't shut down properly

**Solution:**
```bash
# Kill all QEMU processes
pkill -9 -f qemu-system-riscv64

# Wait a moment
sleep 2

# Retry tests
pytest tests/ -v
```

### Issue 2: "Command 'pytest' not found"

**Cause:** Virtual environment not activated

**Solution:**
```bash
# Activate virtual environment
cd ~/software-testing-project/xv6-test-framework
source venv/bin/activate

# You should see (venv) in your prompt
# Now pytest should work
pytest --version
```

### Issue 3: xv6 Compilation Fails

**Symptom:**
```
riscv64-unknown-elf-gcc: command not found
```

**Solution:**
```bash
cd ~/software-testing-project/xv6-riscv

# Fix Makefile to use correct toolchain
sed -i 's/riscv64-unknown-elf-/riscv64-linux-gnu-/g' Makefile

# Clean and rebuild
make clean
make
```

### Issue 4: Tests Timeout

**Symptom:** Tests hang or show "Timeout" errors

**Solution:**
```bash
# Option 1: Skip slow tests
pytest tests/ -v -m "not slow"

# Option 2: Increase timeout in pytest.ini
# Edit pytest.ini and change:
# timeout = 120  →  timeout = 180
```

### Issue 5: Import Error "No module named 'xv6_harness'"

**Cause:** Missing `__init__.py` or wrong directory

**Solution:**
```bash
# Check files exist
ls src/xv6_harness.py
ls src/__init__.py
ls tests/__init__.py

# If missing, create them
touch src/__init__.py
touch tests/__init__.py

# Retry tests
pytest tests/ -v
```

### Issue 6: DNS Resolution Problems (WSL)

**Symptom:** Can't clone from GitHub in WSL

**Solution:**
```bash
# Fix DNS in WSL
sudo rm /etc/resolv.conf
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
echo "nameserver 8.8.4.4" | sudo tee -a /etc/resolv.conf

# Retry git clone
```

### Getting Help

If you encounter other issues:

1. **Check logs:**
   ```bash
   cat logs/pytest.log
   ```

2. **Run verification script:**
   ```bash
   python verify_setup.py
   ```

3. **Clean environment and restart:**
   ```bash
   # Kill all QEMU processes
   pkill -9 -f qemu-system-riscv64
   
   # Deactivate and reactivate venv
   deactivate
   source venv/bin/activate
   
   # Retry tests
   pytest tests/ -v
   ```

---

## 📁 Project Structure

```
xv6-test-framework/
├── src/
│   ├── __init__.py
│   └── xv6_harness.py         # Core testing framework
├── tests/
│   ├── __init__.py
│   ├── test_basic.py          # Basic tests (12 cases)
│   ├── test_filesystem.py     # Filesystem tests (22 cases)
│   ├── test_process.py        # Process tests (17 cases)
│   └── test_fuzzing.py        # Fuzzing tests (31 cases)
├── reports/                    # Generated test reports
├── logs/                       # Test execution logs
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── verify_setup.py            # Environment verification
└── README.md                   # This file
```

---

## 🔄 Daily Workflow

### Starting a Test Session

```bash
# 1. Open terminal and navigate to project
cd ~/software-testing-project/xv6-test-framework

# 2. Activate virtual environment
source venv/bin/activate

# 3. Clean any leftover processes
pkill -9 -f qemu-system-riscv64

# 4. Run tests
pytest tests/ -v -m "not slow"
```

### After Testing

```bash
# View test report
cat reports/test_report.html

# View logs if needed
cat logs/pytest.log

# Deactivate virtual environment (optional)
deactivate
```

---

## 📚 Additional Resources

- **xv6 Book:** https://pdos.csail.mit.edu/6.828/2021/xv6/book-riscv-rev2.pdf
- **xv6 Source:** https://github.com/mit-pdos/xv6-riscv
- **pytest Documentation:** https://docs.pytest.org/
- **pexpect Documentation:** https://pexpect.readthedocs.io/

---

## 📧 Contact

- **Chen Wei-Yu:** 314553037@...
- **Peng Yi-Qun:** 314551135@...

**GitHub Repository:** https://github.com/YOUR_USERNAME/xv6-test-framework

---

**Last Updated:** December 2024
