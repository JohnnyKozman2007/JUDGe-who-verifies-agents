import subprocess
import sys
import os

def run_script(script_path, args_list):
    print(f"\n======================================")
    print(f"Running {script_path}...")
    print(f"======================================\n")
    result = subprocess.run([sys.executable, "-u", script_path] + args_list)
    if result.returncode != 0:
        print(f"Error running {script_path}")
        sys.exit(result.returncode)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run the JUDGe pipeline.")
    parser.add_argument("--mode", type=str, choices=["pilot", "actual"], default="pilot", help="Run in pilot mode or actual mode.")
    parser.add_argument("--domain", type=str, choices=["all", "math", "code", "science"], default="all", help="Domain to run experiments for.")
    args = parser.parse_args()

    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
    
    script_args = ["--mode", args.mode, "--domain", args.domain]

    # Ask for all inputs upfront so the script can run unattended
    print("\n--- Pipeline Configuration ---")
    overwrite_gen_input = input("Redo generation of answers? This will delete existing generated data and start fresh. (y/n): ")
    overwrite_ver_input = input("Redo verification? This will delete existing verification data and start fresh. (y/n): ")
    overwrite_val_input = input("Redo validation? This will delete existing validation data and start fresh. (y/n): ")
    
    gen_args = script_args + (["--overwrite"] if overwrite_gen_input.lower().strip() == 'y' else [])
    ver_args = script_args + (["--overwrite"] if overwrite_ver_input.lower().strip() == 'y' else [])
    val_args = script_args + (["--overwrite"] if overwrite_val_input.lower().strip() == 'y' else [])

    # Step 1: Load Data (always runs, resumes automatically — only fetches missing items)
    run_script(os.path.join(src_dir, "data_loader.py"), script_args)
    
    # Step 2: Generate candidate answers
    run_script(os.path.join(src_dir, "generate.py"), gen_args)
    
    # Step 3: Run verifications
    run_script(os.path.join(src_dir, "verify.py"), ver_args)
    
    # Step 4: Validate override/missed-failure cases (code domain only).
    run_script(os.path.join(src_dir, "validate_overrides.py"), val_args)
    
    print(f"\n{args.mode.capitalize()} run for domain '{args.domain}' completed successfully.")
