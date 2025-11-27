"""
xv6 基本功能測試
測試 xv6 的啟動、基本命令和 shell 功能
"""

import pytest
import sys
import os

# 將 src 目錄加入 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from xv6_harness import XV6TestHarness


@pytest.fixture(scope="function")
def xv6():
    """
    Pytest fixture: 為每個測試函數提供乾淨的 xv6 實例
    測試前啟動 xv6，測試後自動清理
    """
    harness = XV6TestHarness(
        xv6_path="../xv6-riscv",
        timeout=10,
        debug=True  # 開發階段建議啟用 debug
    )
    
    # 啟動 xv6
    success = harness.start()
    assert success, "無法啟動 xv6"
    
    yield harness  # 提供給測試函數使用
    
    # 測試完成後清理
    harness.stop()


class TestBasicCommands:
    """測試基本 shell 命令"""
    
    def test_echo_command(self, xv6):
        """測試 echo 命令"""
        success, output = xv6.run_command("echo hello world")
        
        assert success, "echo 命令執行失敗"
        assert "hello world" in output, f"echo 輸出不正確: {output}"
    
    def test_ls_command(self, xv6):
        """測試 ls 命令 - 列出檔案"""
        success, output = xv6.run_command("ls")
        
        assert success, "ls 命令執行失敗"
        # xv6 預設應該有這些檔案
        assert "." in output, "ls 應該顯示當前目錄 '.'"
        assert ".." in output, "ls 應該顯示父目錄 '..'"
    
    def test_cat_readme(self, xv6):
        """測試 cat 命令 - 讀取 README 檔案"""
        success, output = xv6.run_command("cat README")
        
        assert success, "cat 命令執行失敗"
        assert len(output) > 0, "README 檔案內容為空"
        # xv6 README 通常包含 "xv6" 字樣
        assert "xv6" in output.lower(), "README 內容異常"
    
    def test_grep_command(self, xv6):
        """測試 grep 命令"""
        # 先用 echo 創建一些輸出，然後用 grep 過濾
        success, output = xv6.run_command("echo hello world")
        assert success
        
        # 測試 grep（注意：xv6 的 grep 功能可能有限）
        success, output = xv6.run_command("grep xv6 README")
        assert success, "grep 命令執行失敗"


class TestFileSystem:
    """測試檔案系統基本操作"""
    
    def test_file_exists_check(self, xv6):
        """測試檔案存在性檢查"""
        # README 應該存在
        assert xv6.check_file_exists("README"), "README 檔案應該存在"
        
        # 不存在的檔案
        assert not xv6.check_file_exists("nonexistent.txt"), \
            "不存在的檔案應該返回 False"
    
    def test_wc_command(self, xv6):
        """測試 wc (word count) 命令"""
        success, output = xv6.run_command("wc README")
        
        assert success, "wc 命令執行失敗"
        # wc 輸出格式: lines words bytes filename
        # 應該包含數字
        assert any(char.isdigit() for char in output), \
            f"wc 輸出應該包含數字: {output}"


class TestProcessManagement:
    """測試行程管理"""
    
    def test_multiple_commands(self, xv6):
        """測試連續執行多個命令"""
        commands = [
            "echo test1",
            "echo test2",
            "echo test3"
        ]
        
        for cmd in commands:
            success, output = xv6.run_command(cmd)
            assert success, f"命令執行失敗: {cmd}"
            expected = cmd.replace("echo ", "")
            assert expected in output, \
                f"命令 '{cmd}' 輸出不正確: {output}"
    
    def test_usertests_exists(self, xv6):
        """檢查 usertests 測試程式是否存在"""
        # usertests 是 xv6 內建的測試程式
        success, output = xv6.run_command("ls")
        assert success, "ls 命令執行失敗"
        
        # 檢查 usertests 是否在檔案列表中
        files = output.split()
        
        # 注意：執行 usertests 會花很長時間，這裡只檢查它是否存在
        # 實際執行會在其他測試中進行
        if "usertests" in files:
            print("\n✓ usertests 程式存在")
        else:
            print(f"\n⚠ 警告: usertests 不在檔案列表中")
            print(f"可用的測試程式: {[f for f in files if not f.startswith('.')]}")
        
        # 這個測試不會失敗，只是檢查並提供資訊
        # 某些 xv6 版本可能沒有 usertests
        assert success, "基本的 ls 命令應該能執行"


class TestShellFeatures:
    """測試 shell 特性"""
    
    def test_command_timeout(self, xv6):
        """測試命令超時處理"""
        # 這個測試驗證框架的超時機制
        # sleep 在 xv6 中可能不存在，但我們可以測試超時邏輯
        
        # 正常命令應該在超時前完成
        success, output = xv6.run_command("echo fast", timeout=5)
        assert success, "快速命令不應該超時"
    
    def test_empty_command(self, xv6):
        """測試空命令（直接按 Enter）"""
        success, output = xv6.run_command("")
        assert success, "空命令應該成功執行（什麼都不做）"
    
    def test_invalid_command(self, xv6):
        """測試不存在的命令"""
        success, output = xv6.run_command("nonexistent_command_xyz")
        
        # xv6 應該返回錯誤訊息
        # 但命令本身應該能執行（不會 hang）
        assert success, "即使命令無效，也應該能返回"


# 可選：測試標記
@pytest.mark.slow
def test_xv6_boot_time(xv6):
    """測試 xv6 啟動時間（標記為慢速測試）"""
    import time
    start = time.time()
    
    # xv6 已經在 fixture 中啟動，這裡測試響應時間
    success, output = xv6.run_command("echo timing")
    
    duration = time.time() - start
    
    assert success
    assert duration < 5, f"命令響應時間過長: {duration}秒"


if __name__ == "__main__":
    # 允許直接執行此測試檔案
    pytest.main([__file__, "-v", "-s"])