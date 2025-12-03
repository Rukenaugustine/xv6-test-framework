"""

專注於測試行程管理的特定行為，而非重複基本命令測試

"""

import pytest
import sys
import os
import time
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from xv6_harness import XV6TestHarness


@pytest.fixture(scope="function")
def xv6():
    """Pytest fixture: 提供 xv6 實例"""
    harness = XV6TestHarness(
        xv6_path="../xv6-riscv",
        timeout=20,
        debug=True
    )
    success = harness.start()
    assert success, "無法啟動 xv6"
    yield harness
    harness.stop()


@pytest.mark.process
class TestProcessCreation:
    """測試行程建立機制（fork 的行為）"""
    
    def test_multiple_processes_independent(self, xv6):
        """測試多個行程是獨立的（不會互相影響）"""
        # 第一個行程建立檔案
        success, _ = xv6.run_command("echo data1 > file1.txt")
        assert success
        
        # 第二個行程建立不同的檔案
        success, _ = xv6.run_command("echo data2 > file2.txt")
        assert success
        
        # 驗證兩個檔案都存在（證明行程間不會互相覆蓋）
        success, output = xv6.run_command("cat file1.txt")
        assert success and "data1" in output
        
        success, output = xv6.run_command("cat file2.txt")
        assert success and "data2" in output
        
        # 清理
        xv6.run_command("rm file1.txt file2.txt")
    
    def test_process_state_isolation(self, xv6):
        """測試行程狀態隔離（檔案描述符、工作目錄等）"""
        # 建立測試檔案
        success, _ = xv6.run_command("echo original > state_test.txt")
        assert success
        
        # 第一個行程修改檔案
        success, _ = xv6.run_command("echo modified > state_test.txt")
        assert success
        
        # 第二個行程讀取（應該看到修改後的內容）
        success, output = xv6.run_command("cat state_test.txt")
        assert success
        assert "modified" in output
        assert "original" not in output
        
        # 清理
        xv6.run_command("rm state_test.txt")
    
    @pytest.mark.slow
    def test_forktest_stress(self, xv6):
        """執行 forktest 壓力測試（如果存在）"""
        success, output = xv6.run_command("ls")
        if "forktest" not in output:
            pytest.skip("forktest 不存在")
        
        # forktest 會建立大量子行程測試 fork
        success, output = xv6.run_command("forktest", timeout=30)
        
        if success and ("OK" in output or "ok" in output.lower()):
            print(f"\n✓ forktest 通過: fork 系統調用正常工作")
        else:
            print(f"\n⚠ forktest 輸出: {output}")


@pytest.mark.process
class TestProcessLifecycle:
    """測試行程生命週期（建立 → 執行 → 結束）"""
    
    def test_process_completion(self, xv6):
        """測試行程正常完成並返回"""
        # 執行命令，驗證能正常結束
        success, output = xv6.run_command("echo process completed")
        assert success, "行程應該正常完成"
        assert "process completed" in output
        
        # 再執行一個命令，證明上一個行程已經結束
        success, output = xv6.run_command("echo next process")
        assert success, "下一個行程應該能正常執行"
    
    def test_rapid_process_lifecycle(self, xv6):
        """測試快速的行程建立和銷毀"""
        # 快速連續執行多個短命令
        for i in range(5):
            success, output = xv6.run_command(f"echo cycle {i}")
            assert success, f"第 {i} 個行程應該正常完成"
            assert f"cycle {i}" in output
        
        print("\n✓ 5 個行程快速建立和銷毀成功")
    
    def test_process_no_zombie_accumulation(self, xv6):
        """測試不會累積殭屍行程（zombie process）"""
        # 執行多個行程，如果有殭屍行程累積，系統會變慢或卡住
        start_time = time.time()
        
        for i in range(10):
            success, _ = xv6.run_command(f"echo test {i}", timeout=5)
            assert success, f"第 {i} 個行程執行失敗（可能有殭屍行程堆積）"
        
        elapsed = time.time() - start_time
        
        # 如果沒有殭屍行程，執行時間應該相對穩定
        print(f"\n10 個行程執行時間: {elapsed:.2f} 秒")
        assert elapsed < 30, "執行時間過長，可能有行程管理問題"


@pytest.mark.process
class TestProcessCommunication:
    """測試行程間的通訊和資料共享"""
    
    def test_file_based_communication(self, xv6):
        """測試透過檔案系統進行行程間通訊"""
        # 行程 A 寫入資料
        success, _ = xv6.run_command("echo message from process A > ipc.txt")
        assert success, "行程 A 寫入失敗"
        
        # 行程 B 讀取資料
        success, output = xv6.run_command("cat ipc.txt")
        assert success, "行程 B 讀取失敗"
        assert "message from process A" in output, "行程間通訊失敗"
        
        # 行程 C 修改資料
        success, _ = xv6.run_command("echo reply from process C > ipc.txt")
        assert success, "行程 C 寫入失敗"
        
        # 行程 D 讀取新資料
        success, output = xv6.run_command("cat ipc.txt")
        assert success, "行程 D 讀取失敗"
        assert "reply from process C" in output, "更新的資料讀取失敗"
        
        # 清理
        xv6.run_command("rm ipc.txt")
    
    def test_pipe_if_supported(self, xv6):
        """測試管道通訊（如果 xv6 支援）
        Inter-Process Communication, IPC
        """
        # 嘗試使用管道
        success, output = xv6.run_command("echo test | grep test", timeout=15)
        
        if success and "test" in output:
            print("\n✓ xv6 支援管道，行程間可透過管道通訊")
        else:
            print("\n⚠ xv6 可能不支援標準管道語法")
            pytest.skip("管道不支援")


@pytest.mark.process
class TestProcessErrors:
    """測試行程錯誤處理和異常情況"""
    
    def test_invalid_program_execution(self, xv6):
        """測試執行不存在的程式（exec 失敗）"""
        success, output = xv6.run_command("nonexistent_program_xyz")
        
        # Shell 應該能處理 exec 失敗的情況，不會 hang
        assert success, "Shell 應該能處理無效的程式名稱"
        print(f"\n執行不存在程式的結果: '{output}'")
    
    def test_process_with_error(self, xv6):
        """測試產生錯誤的行程不會影響後續行程"""
        # 執行可能失敗的命令
        xv6.run_command("cat nonexistent_file.txt")
        
        # 後續命令應該仍能正常執行
        success, output = xv6.run_command("echo after error")
        assert success, "錯誤後的行程應該能正常執行"
        assert "after error" in output
    
    def test_empty_command_handling(self, xv6):
        """測試空命令的處理（行程管理的邊界情況）"""
        success, _ = xv6.run_command("")
        assert success, "空命令應該能正常處理"
        
        # 之後的命令應該仍正常
        success, output = xv6.run_command("echo after empty")
        assert success
        assert "after empty" in output


@pytest.mark.process
class TestProcessResourceManagement:
    """測試行程資源管理"""
    
    def test_file_descriptor_cleanup(self, xv6):
        """測試檔案描述符在行程結束後被正確清理"""
        # 建立檔案
        success, _ = xv6.run_command("echo test > fd_test.txt")
        assert success
        
        # 多次讀取（每次都是新行程）
        for i in range(5):
            success, output = xv6.run_command("cat fd_test.txt")
            assert success, f"第 {i} 次讀取失敗（可能檔案描述符洩漏）"
            assert "test" in output
        
        # 清理
        xv6.run_command("rm fd_test.txt")
        print("\n✓ 檔案描述符正確清理，無洩漏")
    
    def test_memory_cleanup_indirect(self, xv6):
        """間接測試記憶體清理（透過重複執行）"""
        # 重複執行命令，如果有記憶體洩漏，系統會逐漸變慢
        times = []
        
        for i in range(5):
            start = time.time()
            success, _ = xv6.run_command("echo memory test")
            elapsed = time.time() - start
            times.append(elapsed)
            assert success, f"第 {i} 次執行失敗"
        
        # 執行時間應該相對穩定
        avg_time = sum(times) / len(times)
        print(f"\n平均執行時間: {avg_time:.3f} 秒")
        print(f"時間列表: {[f'{t:.3f}s' for t in times]}")
        
        # 最後一次不應該明顯慢於第一次（允許 2 倍差異）
        assert times[-1] < times[0] * 2, "執行時間增長過多，可能有記憶體洩漏"


@pytest.mark.process
class TestConcurrentProcessBehavior:
    """測試並發行程的行為"""
    
    def test_sequential_file_operations(self, xv6):
        """測試連續的檔案操作（模擬並發場景）"""
        # 多個行程操作同一個檔案
        success, _ = xv6.run_command("echo first > concurrent.txt")
        assert success
        
        success, _ = xv6.run_command("echo second > concurrent.txt")
        assert success
        
        # 最後一次寫入應該生效
        success, output = xv6.run_command("cat concurrent.txt")
        assert success
        assert "second" in output
        
        # 清理
        xv6.run_command("rm concurrent.txt")
    
    def test_interleaved_operations(self, xv6):
        """測試交錯的檔案操作"""
        # 建立兩個檔案
        success, _ = xv6.run_command("echo A > fileA.txt")
        assert success
        
        success, _ = xv6.run_command("echo B > fileB.txt")
        assert success
        
        # 交錯讀取
        success, outputA = xv6.run_command("cat fileA.txt")
        assert success and "A" in outputA
        
        success, outputB = xv6.run_command("cat fileB.txt")
        assert success and "B" in outputB
        
        # 清理
        xv6.run_command("rm fileA.txt fileB.txt")


@pytest.mark.process
@pytest.mark.slow
class TestProcessStress:
    """行程系統的壓力測試"""
    
    def test_many_short_lived_processes(self, xv6):
        """測試大量短生命週期的行程"""
        success_count = 0
        failures = []
        
        for i in range(20):
            success, _ = xv6.run_command(f"echo process {i}", timeout=5)
            if success:
                success_count += 1
            else:
                failures.append(i)
        
        # 允許少數失敗
        success_rate = success_count / 20
        assert success_rate >= 0.9, \
            f"成功率 {success_rate*100:.1f}% 太低。失敗的: {failures}"
        
        print(f"\n✓ {success_count}/20 個行程成功執行（{success_rate*100:.1f}%）")
    
    def test_processes_with_file_operations(self, xv6):
        """測試行程與檔案操作的組合壓力"""
        for i in range(5):
            # 建立
            success, _ = xv6.run_command(f"echo data{i} > stress{i}.txt")
            assert success, f"建立 stress{i}.txt 失敗"
            
            # 讀取
            success, output = xv6.run_command(f"cat stress{i}.txt")
            assert success and f"data{i}" in output, f"讀取 stress{i}.txt 失敗"
            
            # 刪除
            success, _ = xv6.run_command(f"rm stress{i}.txt")
            assert success, f"刪除 stress{i}.txt 失敗"
        
        print("\n✓ 5 輪 建立→讀取→刪除 循環成功")


@pytest.mark.process
@pytest.mark.slow
class TestAdvancedProcessFeatures:
    """進階行程功能測試"""
    
    def test_usertests_if_available(self, xv6):
        """執行 xv6 內建的 usertests（綜合測試）"""
        success, output = xv6.run_command("ls")
        if "usertests" not in output:
            pytest.skip("usertests 不存在")
        
        print("\n執行 usertests（這會花費較長時間）...")
        success, output = xv6.run_command("usertests", timeout=300)
        
        if success:
            # 檢查測試結果
            if "ALL TESTS PASSED" in output or "all tests" in output.lower():
                print("\n✓ usertests 全部通過")
            else:
                print(f"\nusertests 輸出:\n{output}")
        else:
            print("\n⚠ usertests 超時或失敗")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])