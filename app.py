"""
=============================================================================
Digital Shield – Smart Emergency Safety System
app.py  |  Concurrent Launcher Script for User and Operator Apps
=============================================================================
Description:
    Launches the split applications.
    Usage:
        python app.py [both | user | operator]
        
    - Defaults to launching both services concurrently.
    - User Application runs on http://127.0.0.1:5000/
    - Operator Console runs on http://127.0.0.1:5001/
=============================================================================
"""

import sys
import os
import subprocess
import time

def start_process(script_name, port):
    """Starts a python script in a subprocess using the current virtualenv Python."""
    # Detect the current python interpreter (might be virtualenv)
    python_bin = sys.executable
    
    print(f"[Launcher] Starting {script_name} on Port {port}...")
    
    # We open standard outputs to make it readable in the console
    process = subprocess.Popen(
        [python_bin, script_name],
        stdout=None,
        stderr=None,
        env=os.environ.copy()
    )
    return process

def main():
    mode = "both"
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("user", "operator", "both"):
            mode = arg

    processes = []
    
    try:
        if mode in ("user", "both"):
            p_user = start_process("app_user.py", 5000)
            processes.append(p_user)
            
        # Small delay to let database init finish if launching both
        if mode == "both":
            time.sleep(1)
            
        if mode in ("operator", "both"):
            p_operator = start_process("app_operator.py", 5001)
            processes.append(p_operator)

        print("\n" + "=" * 60)
        print("  Digital Shield Multi-Service System Started")
        if mode in ("user", "both"):
            print("  - User Safety App     : http://127.0.0.1:5000")
        if mode in ("operator", "both"):
            print("  - Operator Console    : http://127.0.0.1:5001")
        print("  Press Ctrl+C to stop all services.")
        print("=" * 60 + "\n")

        # Keep launcher running
        while True:
            # Check if any process has exited unexpectedly
            for p in processes:
                if p.poll() is not None:
                    print(f"\n[Launcher] Process {p.pid} exited with code {p.returncode}. Shutting down remaining services...")
                    raise KeyboardInterrupt
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[Launcher] Stopping all services...")
        for p in processes:
            try:
                # Terminate subprocesses
                p.terminate()
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()
            except Exception as e:
                print(f"[Launcher] Error terminating process: {e}")
        print("[Launcher] Services stopped. Safe journey.")

if __name__ == "__main__":
    main()
