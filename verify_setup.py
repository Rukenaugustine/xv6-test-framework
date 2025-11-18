#!/usr/bin/env python3
"""驗證環境設置的腳本 - 修正版"""

import sys
import subprocess
import shutil
import os

def check_command(cmd, name):
    """檢查命令是否可用"""
    if shutil.which(cmd):
        print(f"✓ {name} 已安裝: {shutil.which(cmd)}")
        return True
    else:
        print(f"✗ {name} 未找到")
        return False

def check_riscv_gcc():
    """檢查 RISC-V GCC (支援多種命名)"""
    gcc_variants = [
        ("riscv64-linux-gnu-gcc", "RISC-V GCC (linux-gnu)"),
        ("riscv64-unknown-elf-gcc", "RISC-V GCC (unknown-elf)"),
        ("riscv64-elf-gcc", "RISC-V GCC (elf)"),
    ]
    
    for cmd, name in gcc_variants:
        if shutil.which(cmd):
            print(f"✓ {name} 已安裝: {shutil.which(cmd)}")
            return True, cmd
    
    print(f"✗ RISC-V GCC 未找到 (嘗試過: {', '.join([v[0] for v in gcc_variants])})")
    return False, None

def check_python_module(module, name):
    """檢查 Python 模組是否可用"""
    try:
        __import__(module)
        print(f"✓ {name} 已安裝")
        return True
    except ImportError:
        print(f"✗ {name} 未安裝")
        return False

def check_xv6_makefile():
    """檢查 xv6 Makefile 並顯示工具鏈配置"""
    makefile_path = "../xv6-riscv/Makefile"
    if os.path.isfile(makefile_path):
        try:
            with open(makefile_path, 'r') as f:
                content = f.read()
                # 尋找 TOOLPREFIX
                for line in content.split('\n'):
                    if 'TOOLPREFIX' in line and not line.strip().startswith('#'):
                        print(f"  Makefile 配置: {line.strip()}")
                        return True
        except Exception as e:
            print(f"  ⚠ 無法讀取 Makefile: {e}")
    return False

def main():
    print("=== xv6 測試框架環境檢查 (修正版) ===\n")
    
    all_ok = True
    
    print("檢查系統工具:")
    all_ok &= check_command("git", "Git")
    all_ok &= check_command("qemu-system-riscv64", "QEMU RISC-V")
    
    # 使用新的 RISC-V GCC 檢查
    gcc_ok, gcc_cmd = check_riscv_gcc()
    all_ok &= gcc_ok
    
    if gcc_ok:
        print(f"\n檢查 xv6 Makefile 配置:")
        check_xv6_makefile()
    
    print("\n檢查 Python 版本:")
    py_version = sys.version_info
    if py_version >= (3, 8):
        print(f"✓ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        print(f"✗ Python 版本太舊 ({py_version.major}.{py_version.minor})")
        all_ok = False
    
    print("\n檢查 Python 套件:")
    all_ok &= check_python_module("pytest", "pytest")
    all_ok &= check_python_module("pexpect", "pexpect")
    
    print("\n檢查專案結構:")
    dirs = ['tests', 'src', 'reports', 'logs', 'venv']
    for d in dirs:
        if os.path.isdir(d):
            print(f"✓ {d}/ 目錄存在")
        else:
            print(f"✗ {d}/ 目錄不存在")
            if d != 'venv':  # venv 缺失不算錯誤
                all_ok = False
    
    print("\n檢查 xv6-riscv:")
    xv6_kernel = "../xv6-riscv/kernel/kernel"
    xv6_dir = "../xv6-riscv"
    
    if os.path.isfile(xv6_kernel):
        print(f"✓ xv6 已編譯")
    elif os.path.isdir(xv6_dir):
        print(f"⚠ xv6 目錄存在但尚未編譯")
        print(f"  執行: cd ../xv6-riscv && make")
    else:
        print(f"✗ xv6-riscv 目錄不存在")
        print(f"  執行: cd .. && git clone https://github.com/mit-pdos/xv6-riscv.git")
        all_ok = False
    
    print("\n" + "="*60)
    if all_ok:
        print("✅ 環境設置完成！可以開始開發測試框架")
        print(f"\n當前位置：{os.getcwd()}")
        print(f"\n💡 提示：")
        print(f"  - 啟動虛擬環境: source venv/bin/activate")
        print(f"  - 執行測試: pytest tests/")
        if gcc_cmd:
            print(f"  - RISC-V GCC: {gcc_cmd}")
        return 0
    else:
        print("❌ 部分組件缺失，請參考上述訊息修復")
        
        print("\n🔧 修復建議:")
        if not gcc_ok:
            print("  1. 安裝 RISC-V 工具鏈:")
            print("     sudo apt-get install gcc-riscv64-linux-gnu")
            print("  2. 或修改 xv6 Makefile:")
            print("     cd ../xv6-riscv")
            print("     sed -i 's/riscv64-unknown-elf-/riscv64-linux-gnu-/g' Makefile")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
