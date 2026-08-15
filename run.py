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

    # Step 1: Load Data (always runs, resumes automatically — only fetches missing items)
    run_script(os.path.join(src_dir, "data_loader.py"), script_args)
    
    # Step 2: Generate candidate answers
    overwrite_gen = input("\nRedo generation of answers? This will delete existing generated data and start fresh. (y/n): ")
    gen_args = script_args + (["--overwrite"] if overwrite_gen.lower().strip() == 'y' else [])
    run_script(os.path.join(src_dir, "generate.py"), gen_args)
    
    # Step 3: Run verifications
    overwrite_ver = input("\nRedo verification? This will delete existing verification data and start fresh. (y/n): ")
    ver_args = script_args + (["--overwrite"] if overwrite_ver.lower().strip() == 'y' else [])
    run_script(os.path.join(src_dir, "verify.py"), ver_args)
    
    print(f"\n{args.mode.capitalize()} run for domain '{args.domain}' completed successfully.")
