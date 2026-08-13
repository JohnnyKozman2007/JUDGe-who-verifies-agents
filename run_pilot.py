import subprocess
import sys
import os

def run_script(script_path):
    print(f"\n======================================")
    print(f"Running {script_path}...")
    print(f"======================================\n")
    result = subprocess.run([sys.executable, "-u", script_path])
    if result.returncode != 0:
        print(f"Error running {script_path}")
        sys.exit(result.returncode)

if __name__ == "__main__":
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
    
    # Step 1: Load Data
    run_script(os.path.join(src_dir, "data_loader.py"))
    
    # Step 2: Generate candidate answers
    run_script(os.path.join(src_dir, "generate.py"))
    
    # Step 3: Run verifications
    run_script(os.path.join(src_dir, "verify.py"))
    
    # Step 4: Evaluate
    run_script(os.path.join(src_dir, "evaluate.py"))
    
    print("\nPilot run completed successfully.")
