import pytest
import pexpect
import subprocess
import os
import time
import hashlib

from nspire_keymap import KeyMap
from typing import Optional, TextIO


def debug_print(message: str) -> None:
    """Just a wrapper lol"""
    print(f"[DEBUG] {message}")


def md5_file(path: str) -> str:
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


class EmulatorController:
    def __init__(
        self,
        boot1_path: str,
        flash_path: str,
        firebird_headless_path: str,
        snapshot_path: Optional[str] = None,
        rdbg_port: int = 3334,
        gdb_port: int = 3333,
        realtime: bool = True,
        output_gif_path: Optional[str] = None,
    ) -> None:
        self.boot1_path = boot1_path
        self.flash_path = flash_path
        self.firebird_headless_path = firebird_headless_path
        self.snapshot_path = snapshot_path
        self.rdbg_port = rdbg_port
        self.gdb_port = gdb_port
        self.realtime = realtime
        self.output_gif_path = output_gif_path
        self.child: Optional[pexpect.spawn] = None
        self.logfile: Optional[TextIO] = None

    """
    Common
    """

    def power_on(self) -> None:
        cmd_parts = [
            self.firebird_headless_path,
            "--boot1",
            self.boot1_path,
            "--flash",
            self.flash_path,
        ]
        if self.snapshot_path:
            cmd_parts.extend(["--snapshot", self.snapshot_path])
        cmd_parts.extend(
            ["--rdbg-port", str(self.rdbg_port), "--gdb-port", str(self.gdb_port)]
        )
        if self.realtime:
            cmd_parts.append("--realtime")
        if self.output_gif_path:
            cmd_parts.extend(["--write-gif", self.output_gif_path])
        cmd = " ".join(cmd_parts)
        debug_print(f"Starting headless emulator with command: {cmd}")
        self.child = pexpect.spawn(cmd, encoding="utf-8")
        self.logfile = open("/tmp/emulator_output.log", "w")
        self.child.logfile = self.logfile
        debug_print("Logfile set up at /tmp/emulator_output.log")

    def wait_for_message(self, message: str, timeout: int = 60) -> None:
        debug_print(f"Waiting for '{message}' message...")
        self.child.expect(message, timeout=timeout)

    def sleep(self, seconds: int) -> None:
        debug_print(f"Sleeping for {seconds} seconds...")
        time.sleep(seconds)

    def power_down(self) -> None:
        debug_print("Sending stop command via rdbg...")
        self.sleep(1)
        stop_cmd = f"echo stop | nc -q 1 localhost {self.rdbg_port}"
        subprocess.run(stop_cmd, shell=True, check=True, capture_output=True)
        debug_print("Waiting for the emulator process to exit...")
        self.child.expect(pexpect.EOF)
        debug_print("Closing logfile...")
        self.logfile.close()
        debug_print("Terminating child process if still running...")
        if self.child.isalive():
            self.child.terminate()

    """
    File hanlding 
    """

    def send_file(self, file_path: str, dest_file_path: str = "/") -> None:
        debug_print(f"Sending file {file_path} to {dest_file_path}...")
        send_cmd = f"echo 'ln st {dest_file_path}\n ln s {file_path}' | nc -q 0 localhost {self.rdbg_port}"
        subprocess.run(send_cmd, shell=True, check=True)

    def take_snapshot(self, path: str) -> None:
        debug_print(f"Saving snapshot to {path} via rdbg...")
        snapshot_cmd = f"echo 'ws {path}' | nc -q 0 localhost {self.rdbg_port}"
        subprocess.run(snapshot_cmd, shell=True, check=True)

    def take_screenshot(self, path: str) -> None:
        debug_print(f"Taking screenshot to {path} via rdbg...")
        scr_cmd = f"echo 'scr {path}' | nc -q 0 localhost {self.rdbg_port}"
        subprocess.run(scr_cmd, shell=True, check=True)

    """
    Key handling 
    """

    def press_key(self, keycode: KeyMap) -> None:
        debug_print(f"Pressing key {keycode}...")
        row, col = keycode.value
        key_cmd = f"echo 'key {row} {col} 1' | nc -q 0 localhost {self.rdbg_port}"
        subprocess.run(key_cmd, shell=True, check=True)

    def release_key(self, keycode: KeyMap) -> None:
        debug_print(f"Releasing key {keycode}...")
        row, col = keycode.value
        key_cmd = f"echo 'key {row} {col} 0' | nc -q 0 localhost {self.rdbg_port}"
        subprocess.run(key_cmd, shell=True, check=True)

    def press_and_release_key(self, keycode: KeyMap, delay: float = 0.5) -> None:
        self.press_key(keycode)
        time.sleep(delay)
        self.release_key(keycode)

    """
    Aggregate helpers (these use the above to do stuff)
    """

    def os_install_to_home(
        self,
        snapshot_path: str,
        screenshot_path: str,
        os_path: str,
    ) -> None:
        self.power_on()
        self.wait_for_message("USB Download is enabled.")
        self.send_file(os_path)
        self.wait_for_message(
            "END TI_LOCALE_initializeDefaultLocale.....",
            timeout=120,
        )
        self.sleep(5)
        self.press_and_release_key(KeyMap._enter)
        self.sleep(2)
        self.take_snapshot(str(snapshot_path))
        self.take_screenshot(str(screenshot_path))


def test_os_install_to_home(
    boot1_path: str,
    flash_path: str,
    os_path: str,
    firebird_headless_path: str,
    workspace_path: str,
) -> None:
    debug_print("Starting emulator automation test...")

    snapshot_path = os.path.join(workspace_path, "snapshot.bin")
    screenshot_path = os.path.join(workspace_path, "output.rgb")

    try:
        # Power on + OS install to home screen
        emu = EmulatorController(boot1_path, flash_path, firebird_headless_path)
        emu.os_install_to_home(snapshot_path, screenshot_path, os_path)
    finally:
        emu.power_down()

    # Verify files exist
    assert os.path.exists(snapshot_path)
    assert os.path.exists(screenshot_path)

    # Compute MD5s
    screenshot_md5 = md5_file(screenshot_path)

    print(screenshot_md5)
