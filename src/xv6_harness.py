"""
xv6 測試框架核心模組
使用 pexpect 控制 QEMU 中運行的 xv6 作業系統
"""

import pexpect
import time
import os
import signal
from typing import Optional, List, Tuple


class XV6TestHarness:
    """xv6 測試框架主類別"""

    def __init__(self,
                 xv6_path: str = "../xv6-riscv",
                 timeout: int = 30,
                 debug: bool = False):
        """
        初始化測試框架

        Args:
            xv6_path: xv6-riscv 原始碼路徑
            timeout: 預設命令超時時間（秒）
            debug: 是否啟用除錯模式（顯示所有互動）
        """
        self.xv6_path = os.path.abspath(xv6_path)
        self.timeout = timeout
        self.debug = debug
        # 我宣告一個叫做 self.process 的變數，它一開始是空的 (None)，但在未來它應該要存放一個 pexpect.spawn 類型的物件。
        self.process: Optional[pexpect.spawn] = None 
        self.boot_timeout = 60  # 啟動超時時間

    def start(self) -> bool:
        """
        啟動 xv6 在 QEMU 中

        Returns:
            bool: 啟動成功返回 True，否則返回 False
        """
        try:
            # 確認 xv6 目錄存在
            if not os.path.isdir(self.xv6_path):
                raise FileNotFoundError(f"xv6 目錄不存在: {self.xv6_path}")

            # 確認 kernel 已編譯
            kernel_path = os.path.join(self.xv6_path, "kernel", "kernel")
            if not os.path.isfile(kernel_path):
                raise FileNotFoundError(
                    f"xv6 kernel 未編譯，請先執行: cd {self.xv6_path} && make"
                )

            # 啟動 QEMU
            # 使用 make qemu-gdb 可以不掛在前台，或直接用 qemu 命令
            cmd = f"make -C {self.xv6_path} qemu"

            if self.debug:
                print(f"[DEBUG] 執行命令: {cmd}")

            # spawn QEMU 進程
            self.process = pexpect.spawn(
                cmd,
                timeout=self.boot_timeout,
                encoding='utf-8',
                echo=False
            )

            # 等待 shell 提示符 '$'
            # xv6 啟動後會顯示 "init: starting sh" 然後是 '$'
            self.process.expect(r'\$ ', timeout=self.boot_timeout)

            if self.debug:
                print("[DEBUG] xv6 啟動成功，shell 已就緒")

            return True

        except pexpect.TIMEOUT:
            print(f"[ERROR] xv6 啟動超時（{self.boot_timeout}秒）")
            return False
        except pexpect.EOF:
            print("[ERROR] xv6 進程意外終止")
            if self.process:
                print(f"[ERROR] 輸出: {self.process.before}")
            return False
        except Exception as e:
            print(f"[ERROR] 啟動 xv6 失敗: {e}")
            return False

    def run_command(self,
                    command: str,
                    timeout: Optional[int] = None) -> Tuple[bool, str]:
        """
        在 xv6 shell 中執行命令並獲取輸出

        Args:
            command: 要執行的命令
            timeout: 命令超時時間（秒），None 則使用預設值

        Returns:
            Tuple[bool, str]: (是否成功, 輸出內容)
        """
        if not self.process:
            return False, "Error: xv6 未啟動"

        if timeout is None:
            timeout = self.timeout

        try:
            if self.debug:
                print(f"[DEBUG] 執行命令: {command}")

            # 發送命令
            self.process.sendline(command)

            # 等待命令執行完成，shell 提示符再次出現
            self.process.expect(r'\$ ', timeout=timeout)

            # 獲取輸出（在提示符之前的內容）
            output = self.process.before

            # 清理輸出：移除命令本身的回顯
            lines = output.split('\n')
            # command in line[0]: 只有當「我的指令 (command)」出現在「第一行 (lines[0])」裡面時，才刪除
            if lines and command in lines[0]:
                lines = lines[1:]  # 移除第一行（命令回顯）

            clean_output = '\n'.join(lines).strip()

            if self.debug:
                print(f"[DEBUG] 輸出:\n{clean_output}")

            return True, clean_output

        except pexpect.TIMEOUT:
            error_msg = f"命令超時: {command}"
            if self.debug:
                print(f"[DEBUG] {error_msg}")
            return False, error_msg
        except pexpect.EOF:
            error_msg = "xv6 進程意外終止"
            if self.debug:
                print(f"[DEBUG] {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"執行命令失敗: {e}"
            if self.debug:
                print(f"[DEBUG] {error_msg}")
            return False, error_msg

    def expect_output(self,
                      pattern: str,
                      timeout: Optional[int] = None) -> Tuple[bool, str]:
        """
        等待特定輸出模式出現（使用正規表達式）

        Args:
            pattern: 要匹配的正規表達式模式
            timeout: 超時時間（秒）

        Returns:
            Tuple[bool, str]: (是否匹配成功, 匹配到的內容)
        """
        if not self.process:
            return False, "Error: xv6 未啟動"

        if timeout is None:
            timeout = self.timeout

        try:
            self.process.expect(pattern, timeout=timeout)
            matched = self.process.after
            return True, matched
        except pexpect.TIMEOUT:
            return False, f"未在 {timeout} 秒內找到模式: {pattern}"
        except Exception as e:
            return False, f"等待輸出失敗: {e}"

    def check_file_exists(self, filename: str) -> bool:
        """
        檢查檔案是否存在於 xv6 檔案系統中

        Args:
            filename: 檔案名稱

        Returns:
            bool: 檔案存在返回 True
        """
        success, output = self.run_command("ls")
        if not success:
            return False

        # 檢查 ls 輸出中是否包含檔案名
        return filename in output.split()

    def stop(self) -> bool:
        """
        停止 xv6/QEMU

        Returns:
            bool: 成功停止返回 True
        """
        if not self.process:
            return True

        try:
            if self.debug:
                print("[DEBUG] 停止 xv6...")

            # QEMU 的退出組合鍵是 Ctrl-A X
            # 但在 pexpect 中我們直接終止進程更可靠
            self.process.terminate(force=True)
            # wait() 的作用：「收屍」。如果不做這一步，死掉的 QEMU 就會變成**「殭屍 (Zombie Process)」**
            self.process.wait()

            if self.debug:
                print("[DEBUG] xv6 已停止")

            self.process = None
            return True

        except Exception as e:
            if self.debug:
                print(f"[DEBUG] 停止 xv6 時發生錯誤: {e}")
            return False

    def __enter__(self):
        """支援 with 語句的上下文管理"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """自動清理資源"""
        self.stop()

    def __del__(self):
        """析構函數：確保進程被清理"""
        if self.process:
            self.stop()
