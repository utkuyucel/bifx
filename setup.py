#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path


def check_venv():
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if not in_venv:
        print("⚠️  WARNING: Virtual environment not detected!")
        print("It's recommended to run this in a virtual environment.")
        print("\nTo create and activate a virtual environment:")
        print("  python3 -m venv venv")
        print("  source venv/bin/activate  # On Linux/Mac")
        print("  venv\\Scripts\\activate   # On Windows")
        response = input("\nContinue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)


def install_dependencies():
    print("📦 Installing dependencies from requirements.txt...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)


def verify_structure():
    print("\n🔍 Verifying project structure...")
    
    required_dirs = ["data/raw", "features", "core"]
    required_files = [
        "config.py", 
        "run_pipeline.py",
        "core/data_loader.py",
        "core/feature_engine.py",
        "core/index_calculator.py",
        "core/backtest.py"
    ]
    
    all_ok = True
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            print(f"❌ Missing directory: {dir_path}")
            all_ok = False
        else:
            print(f"✅ {dir_path}")
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Missing file: {file_path}")
            all_ok = False
        else:
            print(f"✅ {file_path}")
    
    if all_ok:
        print("\n✅ Project structure verified")
    else:
        print("\n⚠️  Some files or directories are missing")
        sys.exit(1)


def main():
    print("=" * 60)
    print("BIFX Setup Script")
    print("=" * 60)
    
    check_venv()
    install_dependencies()
    verify_structure()
    
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Review config.py to adjust date ranges and parameters")
    print("  2. (Optional) Add manual CDS data to data/raw/cds_manual.csv")
    print("  3. Run the pipeline: python run_pipeline.py")
    print("\nTo add custom features:")
    print("  - Create a new .py file in features/")
    print("  - Implement compute(data) -> pd.Series")
    print("  - Run the pipeline — feature auto-discovered!")


if __name__ == "__main__":
    main()
