import pytest
import pexpect
import subprocess
import os
import time

def debug_print(message: str) -> None:
    """Utility function for debug printing."""
    print(f"[DEBUG] {message}")

def test_emulator_automation():
    debug_print("Starting emulator automation test...")
    # Paths to expand
    boot1_path = os.path.expanduser("~/Desktop/nspire_investigation/ti_nspire_cx_ii_bootfiles/injected_btrom.img(1).tns")
    flash_path = os.path.expanduser("~/Desktop/nspire_investigation/ti_nspire_cx_ii_bootfiles/nspire_cx_ii_flash")
    gif_path = "/tmp/output.gif"
    
    # Command to run the headless emulator
    cmd = f"./firebird-headless --boot1 {boot1_path} --flash {flash_path} --rdbg-port 3334 --gdb-port 3333 --write-gif {gif_path} --realtime"
    debug_print(f"Starting headless emulator with command: {cmd}")
    # Start pexpect process
    child = pexpect.spawn(cmd, encoding='utf-8')

    # Set up logfile to write output to a file
    logfile = open('/tmp/emulator_output.log', 'w')
    child.logfile = logfile
    debug_print("Logfile set up at /tmp/emulator_output.log")

    try:
        debug_print("Waiting for 'USB Download is enabled.' message...")
        # Wait for "USB Download is enabled." in the output
        child.expect("USB Download is enabled.", timeout=60)

        debug_print("Running firebird-send command to send TCO2 file...")
        # Run the firebird-send command
        tco2_path = os.path.expanduser("~/Desktop/nspire_investigation/6.3/TI-NspireCXII-6.3.0.119.tco2")
        send_cmd = f"/home/ryan/Desktop/nspire_investigation/firebird_naievil/core/./firebird-send {tco2_path} /"
        subprocess.run(send_cmd, shell=True, check=True)

        debug_print("Waiting for 'END TI_LOCALE_initializeDefaultLocale.....' message...")
        # Wait for "END TI_LOCALE_initializeDefaultLocale....." in the output
        child.expect("END TI_LOCALE_initializeDefaultLocale.....", timeout=120)

        debug_print("Waiting 15 seconds for the home menu to load...")
        # Just wait for the home menu
        time.sleep(15)

        debug_print("Saving snapshot via rdbg...")
        # Save snapshot via rdbg
        snapshot_cmd = "echo 'ws /tmp/snapshot.bin' | nc -q 1 localhost 3334"
        subprocess.run(snapshot_cmd, shell=True, check=True)
        
        debug_print("Sending stop command via rdbg...")
        # Run the stop command via nc
        stop_cmd = "echo stop | nc -q 1 localhost 3334"
        subprocess.run(stop_cmd, shell=True, check=True)

        debug_print("Waiting for the emulator process to exit...")
        # Wait for the process to exit
        child.expect(pexpect.EOF)

    finally:
        debug_print("Closing logfile...")
        # Close the logfile
        logfile.close()

        debug_print("Terminating child process if still running...")
        # Terminate the child process if still running
        if child.isalive():
            child.terminate()
        
        debug_print("Sleeping for 1 second...")
        # Sleep for 1 second
        time.sleep(1)
        
        debug_print("Extracting the last frame from GIF to PNG using ffmpeg...")
        # Extract the last frame from GIF to PNG using ffmpeg
        ffmpeg_cmd = "ffmpeg -i /tmp/output.gif -vf \"reverse\" -vframes 1 /tmp/last.png"
        subprocess.run(ffmpeg_cmd, shell=True, check=True)