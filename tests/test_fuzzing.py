"""
xv6 內核強健性測試 - 模糊測試 (Fuzzing)
向系統調用發送邊界和格式錯誤的輸入，測試內核的強健性


"""

import pytest
import sys
import os
import random
import string

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


@pytest.mark.fuzzing
class TestInvalidFileNames:
    """測試無效的檔案名稱"""
    
    def test_empty_filename(self, xv6):
        """測試空檔案名"""
        # 嘗試建立空檔案名的檔案
        success, output = xv6.run_command('echo test > ""')
        # 系統應該能處理，不會 crash
        assert success, "系統應該能處理空檔案名"
        print(f"\n空檔案名處理: {output[:100]}")
    
    def test_very_long_filename(self, xv6):
        """測試超長檔案名（超過 xv6 限制）"""
        # xv6 檔案名限制是 14 字元
        long_name = "a" * 50 + ".txt"
        
        success, output = xv6.run_command(f"echo test > {long_name}")
        # 系統應該拒絕或截斷，但不會 crash
        assert success, "系統應該能處理超長檔案名"
        print(f"\n超長檔案名 ({len(long_name)} 字元) 處理結果")
    
    def test_special_characters_in_filename(self, xv6):
        """測試檔案名中的特殊字元"""
        # 測試各種特殊字元
        special_names = [
            "file*.txt",      # 萬用字元
            "file?.txt",      # 問號
            "file;.txt",      # 分號
            "file|.txt",      # 管道
            "file&.txt",      # AND 符號
        ]
        
        for filename in special_names:
            success, output = xv6.run_command(f"echo test > {filename}")
            assert success, f"系統應該能處理特殊字元檔案名: {filename}"
            print(f"\n特殊字元 '{filename}': 已處理")
    
    def test_dot_filenames(self, xv6):
        """測試特殊的點檔案名"""
        # 測試 . 和 .. 作為檔案名
        success, _ = xv6.run_command("echo test > .")
        assert success, "系統應該能處理 . 作為檔案名"
        
        success, _ = xv6.run_command("echo test > ..")
        assert success, "系統應該能處理 .. 作為檔案名"
    
    def test_null_in_filename(self, xv6):
        """測試包含空白字元的檔案名"""
        # 測試空格
        success, _ = xv6.run_command("echo test > 'file name.txt'")
        assert success, "系統應該能處理包含空格的檔案名"


@pytest.mark.fuzzing
class TestInvalidFileOperations:
    """測試無效的檔案操作"""
    
    def test_read_nonexistent_file(self, xv6):
        """測試讀取不存在的檔案"""
        # 生成隨機不存在的檔案名
        random_name = ''.join(random.choices(string.ascii_letters, k=10)) + ".txt"
        
        success, output = xv6.run_command(f"cat {random_name}")
        assert success, "讀取不存在檔案應該能處理"
        print(f"\n讀取不存在檔案 '{random_name}': 已處理")
    
    def test_delete_nonexistent_file(self, xv6):
        """測試刪除不存在的檔案"""
        success, output = xv6.run_command("rm nonexistent_xyz_file.txt")
        assert success, "刪除不存在檔案應該能處理"
    
    def test_cat_directory(self, xv6):
        """測試 cat 一個目錄"""
        success, output = xv6.run_command("cat .")
        assert success, "cat 目錄應該能處理"
        print(f"\ncat 目錄結果: {output[:100]}")
    
    def test_write_to_readonly_location(self, xv6):
        """測試寫入到唯讀位置"""
        # 嘗試覆寫系統檔案
        success, output = xv6.run_command("echo test > README")
        # 系統可能允許或拒絕，但不應該 crash
        assert success, "寫入 README 應該能處理"
    
    def test_multiple_slashes_in_path(self, xv6):
        """測試路徑中的多個斜線"""
        success, output = xv6.run_command("cat .//README")
        assert success, "多個斜線應該能處理"
        
        success, output = xv6.run_command("cat ././README")
        assert success, "多個 ./ 應該能處理"


@pytest.mark.fuzzing
class TestBoundaryValues:
    """測試邊界值"""
    
    def test_zero_length_write(self, xv6):
        """測試寫入零長度資料"""
        success, _ = xv6.run_command("echo > zero.txt")
        assert success, "零長度寫入應該能處理"
        
        # 驗證檔案存在
        success, output = xv6.run_command("cat zero.txt")
        assert success
    
    def test_very_long_command_line(self, xv6):
        """測試超長命令列"""
        # 建立一個很長的 echo 命令
        long_string = "a" * 100
        success, output = xv6.run_command(f"echo {long_string}")
        
        # 系統應該能處理或截斷
        assert success, "超長命令列應該能處理"
        print(f"\n超長命令列處理成功 (長度: {len(long_string)})")
    
    def test_many_arguments(self, xv6):
        """測試大量參數"""
        # 傳遞多個參數給 echo
        args = " ".join([f"arg{i}" for i in range(20)])
        success, output = xv6.run_command(f"echo {args}")
        
        assert success, "大量參數應該能處理"
    
    def test_maximum_open_files(self, xv6):
        """測試最大開啟檔案數"""
        # 快速建立多個檔案
        for i in range(10):
            success, _ = xv6.run_command(f"echo data{i} > fuzz_file{i}.txt", timeout=5)
            if not success:
                print(f"\n達到檔案限制: {i} 個檔案")
                break
        
        # 清理
        for i in range(10):
            xv6.run_command(f"rm fuzz_file{i}.txt", timeout=5)


@pytest.mark.fuzzing
class TestInvalidArguments:
    """測試無效參數"""
    
    def test_cat_with_no_arguments(self, xv6):
        """測試 cat 沒有參數"""
        success, output = xv6.run_command("cat", timeout=5)
        # cat 可能會等待輸入或返回錯誤
        print(f"\ncat 無參數結果: {output[:100] if output else '(無輸出)'}")
    
    def test_rm_with_no_arguments(self, xv6):
        """測試 rm 沒有參數"""
        success, output = xv6.run_command("rm")
        assert success, "rm 無參數應該能處理"
    
    def test_grep_with_invalid_pattern(self, xv6):
        """測試 grep 使用無效模式"""
        success, output = xv6.run_command("grep '' README")
        assert success, "grep 空模式應該能處理"
        
#  據數學邏輯和標準的 Unix grep 行為：
# 「空字串是任何字串的子集合。」
# 所以，當你執行 grep '' README 時，正確的結果應該是「印出 README 的每一行」（等於把整個檔案印出來）。
    
    def test_echo_with_quotes(self, xv6):
        """測試 echo 使用引號"""
        test_cases = [
            'echo "test"',
            "echo 'test'",
            'echo "test with spaces"',
        ]
        
        for cmd in test_cases:
            success, output = xv6.run_command(cmd)
            assert success, f"命令應該能處理: {cmd}"


@pytest.mark.fuzzing
class TestConcurrentFuzzing:
    """測試並發操作的邊界情況"""
    
    def test_rapid_file_creation_deletion(self, xv6):
        """測試快速建立和刪除檔案"""
        filename = "rapid_fuzz.txt"
        
        # 快速重複建立和刪除
        for i in range(5):
            success, _ = xv6.run_command(f"echo iteration{i} > {filename}", timeout=5)
            assert success, f"第 {i} 次建立失敗"
            
            success, _ = xv6.run_command(f"rm {filename}", timeout=5)
            assert success, f"第 {i} 次刪除失敗"
        
        print("\n✓ 快速建立/刪除循環測試通過")
    
    def test_interleaved_read_write(self, xv6):
        """測試交錯的讀寫操作"""
        filename = "interleave.txt"
        
        # 建立
        success, _ = xv6.run_command(f"echo initial > {filename}")
        assert success
        
        # 交錯讀寫
        for i in range(3):
            # 讀
            success, output = xv6.run_command(f"cat {filename}", timeout=5)
            assert success, f"第 {i} 次讀取失敗"
            
            # 寫
            success, _ = xv6.run_command(f"echo update{i} > {filename}", timeout=5)
            assert success, f"第 {i} 次寫入失敗"
        
        # 清理
        xv6.run_command(f"rm {filename}")
    
    def test_same_file_multiple_operations(self, xv6):
        """測試對同一檔案的多種操作"""
        filename = "multi_op.txt"
        
        # 建立
        success, _ = xv6.run_command(f"echo test > {filename}")
        assert success
        
        # 多種操作
        operations = [
            f"cat {filename}",
            f"wc {filename}",
            f"grep test {filename}",
            f"cat {filename}",
        ]
        
        for op in operations:
            success, _ = xv6.run_command(op, timeout=5)
            assert success, f"操作失敗: {op}"
        
        # 清理
        xv6.run_command(f"rm {filename}")


@pytest.mark.fuzzing
class TestResourceExhaustion:
    """測試資源耗盡情況"""
    
    def test_many_small_files(self, xv6):
        """測試建立大量小檔案"""
        max_files = 15
        created = []
        
        for i in range(max_files):
            filename = f"small_{i}.txt"
            success, _ = xv6.run_command(f"echo f{i} > {filename}", timeout=5)
            
            if success:
                created.append(filename)
            else:
                print(f"\n達到檔案系統限制: {i} 個檔案")
                break
        
        print(f"\n成功建立 {len(created)} 個檔案")
        
        # 清理
        for filename in created:
            xv6.run_command(f"rm {filename}", timeout=5)
        
        # 至少應該能建立一些檔案
        assert len(created) > 0, "應該能建立至少一些檔案"
    
    @pytest.mark.slow
    def test_rapid_process_creation(self, xv6):
        """測試快速建立行程"""
        num_processes = 20
        failures = []
        
        for i in range(num_processes):
            success, _ = xv6.run_command(f"echo process{i}", timeout=5)
            if not success:
                failures.append(i)
        
        success_rate = (num_processes - len(failures)) / num_processes
        print(f"\n行程建立成功率: {success_rate*100:.1f}%")
        
        # 允許少數失敗
        assert success_rate >= 0.7, "成功率應該 >= 70%"


@pytest.mark.fuzzing
class TestErrorRecovery:
    """測試錯誤恢復能力"""
    
    def test_recovery_after_invalid_command(self, xv6):
        """測試執行無效命令後的恢復"""
        # 執行無效命令
        xv6.run_command("invalid_command_xyz_123")
        
        # 系統應該能恢復並執行正常命令
        success, output = xv6.run_command("echo recovery test")
        assert success, "系統應該能從錯誤中恢復"
        assert "recovery test" in output
    
    def test_recovery_after_file_error(self, xv6):
        """測試檔案錯誤後的恢復"""
        # 嘗試讀取不存在的檔案
        xv6.run_command("cat nonexistent_file.txt")
        
        # 建立新檔案應該仍能成功
        success, _ = xv6.run_command("echo new file > recovery.txt")
        assert success, "檔案錯誤後應該能建立新檔案"
        
        success, output = xv6.run_command("cat recovery.txt")
        assert success and "new file" in output
        
        # 清理
        xv6.run_command("rm recovery.txt")
    
    def test_multiple_errors_in_sequence(self, xv6):
        """測試連續多個錯誤"""
        error_commands = [
            "cat nonexistent1.txt",
            "rm nonexistent2.txt",
            "invalid_command",
            "grep pattern nonexistent3.txt",
        ]
        
        for cmd in error_commands:
            xv6.run_command(cmd, timeout=5)
        
        # 所有錯誤後，系統應該仍能正常工作
        success, output = xv6.run_command("echo still working")
        assert success, "多個錯誤後系統應該仍能工作"
        assert "still working" in output


@pytest.mark.fuzzing
class TestEdgeCases:
    """測試其他邊界情況"""
    
    def test_command_with_only_spaces(self, xv6):
        """測試只有空格的命令"""
        success, _ = xv6.run_command("   ")
        assert success, "只有空格的命令應該能處理"
    
    def test_repeated_operators(self, xv6):
        """測試重複的操作符"""
        # 測試重複的 >
        success, _ = xv6.run_command("echo test >> double.txt")
        # xv6 可能不支援 >>，但不應該 crash
        assert success, "重複操作符應該能處理"
    
    def test_filename_with_numbers_only(self, xv6):
        """測試純數字檔案名"""
        success, _ = xv6.run_command("echo test > 12345")
        assert success, "純數字檔案名應該能處理"
        
        success, output = xv6.run_command("cat 12345")
        if success:
            assert "test" in output
        
        xv6.run_command("rm 12345")
    
    def test_single_character_filename(self, xv6):
        """測試單字元檔案名"""
        for char in ['a', 'x', 'z', '1']:
            success, _ = xv6.run_command(f"echo test > {char}")
            assert success, f"單字元檔案名 '{char}' 應該能處理"
            xv6.run_command(f"rm {char}")


@pytest.mark.fuzzing
class TestRandomFuzzing:
    """隨機模糊測試"""
    
    def test_random_valid_operations(self, xv6):
        """測試隨機的有效操作組合"""
        operations = [
            lambda: xv6.run_command("echo random test > rand.txt"),
            lambda: xv6.run_command("cat rand.txt"),
            lambda: xv6.run_command("ls"),
            lambda: xv6.run_command("echo update > rand.txt"),
            lambda: xv6.run_command("rm rand.txt"),
        ]
        
        # 隨機執行操作
        for _ in range(10):
            op = random.choice(operations)
            success, _ = op()
            # 不強制要求所有操作都成功（檔案可能不存在等）
            # 但系統應該不會 crash
        
        # 確保系統仍然運作
        success, output = xv6.run_command("echo final test")
        assert success, "隨機操作後系統應該仍能工作"
        assert "final test" in output
    
    @pytest.mark.slow
    def test_stress_with_random_filenames(self, xv6):
        """使用隨機檔案名的壓力測試"""
        created_files = []
        
        for i in range(10):
            # 生成隨機檔案名
            random_name = ''.join(random.choices(string.ascii_lowercase, k=8)) + ".txt"
            success, _ = xv6.run_command(f"echo data{i} > {random_name}", timeout=5)
            
            if success:
                created_files.append(random_name)
        
        print(f"\n建立了 {len(created_files)} 個隨機命名的檔案")
        
        # 清理
        for filename in created_files:
            xv6.run_command(f"rm {filename}", timeout=5)
        
        assert len(created_files) > 0, "應該至少建立一些檔案"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])