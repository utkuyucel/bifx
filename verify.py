#!/usr/bin/env python3

import sys
from pathlib import Path


def check_structure():
    print("🔍 Checking project structure...")

    required_structure = {
        "files": [
            "config.py",
            "run_pipeline.py",
            "setup.py",
            "requirements.txt",
            "README.md",
        ],
        "core_modules": [
            "core/__init__.py",
            "core/data_loader.py",
            "core/feature_engine.py",
            "core/index_calculator.py",
            "core/backtest.py",
        ],
        "features": [
            "features/__init__.py",
            "features/realized_vol.py",
            "features/usdtry_shock.py",
            "features/cds_spike.py",
            "features/sentiment_trends.py",
            "features/vix_level.py",
            "features/correlation_breakdown.py",
            "features/example_double_price.py",
        ],
        "directories": [
            "data/raw",
            "core",
            "features",
        ],
    }

    all_ok = True

    # Check directories
    for directory in required_structure["directories"]:
        path = Path(directory)
        if path.exists() and path.is_dir():
            print(f"  ✅ {directory}/")
        else:
            print(f"  ❌ {directory}/ — MISSING")
            all_ok = False

    # Check all files
    for file_list in [
        required_structure["files"],
        required_structure["core_modules"],
        required_structure["features"],
    ]:
        for file_path in file_list:
            path = Path(file_path)
            if path.exists() and path.is_file():
                print(f"  ✅ {file_path}")
            else:
                print(f"  ❌ {file_path} — MISSING")
                all_ok = False

    return all_ok


def check_imports():
    print("\n📦 Checking Python dependencies...")

    required_packages = [
        "pandas",
        "numpy",
        "yfinance",
        "pytrends",
        "sklearn",
        "scipy",
        "matplotlib",
    ]

    all_ok = True

    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} — NOT INSTALLED")
            all_ok = False

    return all_ok


def check_config():
    print("\n⚙️  Checking configuration...")

    try:
        from config import BacktestConfig, DataConfig, DataSources, FeatureConfig, IndexConfig

        config_classes = [
            ("DataConfig", DataConfig),
            ("FeatureConfig", FeatureConfig),
            ("IndexConfig", IndexConfig),
            ("BacktestConfig", BacktestConfig),
            ("DataSources", DataSources),
        ]

        all_ok = True

        for name, cls in config_classes:
            try:
                cls()
                print(f"  ✅ {name}")
            except Exception as e:
                print(f"  ❌ {name} — ERROR: {e}")
                all_ok = False

        return all_ok

    except Exception as e:
        print(f"  ❌ Failed to import config: {e}")
        return False


def check_modules():
    print("\n🔧 Checking core modules...")

    modules = [
        "core.data_loader",
        "core.feature_engine",
        "core.index_calculator",
        "core.backtest",
    ]

    all_ok = True

    for module_name in modules:
        try:
            __import__(module_name)
            print(f"  ✅ {module_name}")
        except Exception as e:
            print(f"  ❌ {module_name} — ERROR: {e}")
            all_ok = False

    return all_ok


def count_features():
    print("\n🎯 Checking features...")

    try:
        from pathlib import Path

        features_dir = Path("features")
        feature_files = [f for f in features_dir.glob("*.py") if f.name != "__init__.py"]

        print(f"  ✅ Found {len(feature_files)} feature modules:")
        for feature_file in sorted(feature_files):
            print(f"      • {feature_file.stem}")

        return True

    except Exception as e:
        print(f"  ❌ Failed to check features: {e}")
        return False


def main():
    print("=" * 70)
    print("BIFX Installation Verification")
    print("=" * 70)
    print()

    results = {
        "structure": check_structure(),
        "imports": check_imports(),
        "config": check_config(),
        "modules": check_modules(),
        "features": count_features(),
    }

    print("\n" + "=" * 70)
    print("Verification Summary")
    print("=" * 70)

    for check_name, check_result in results.items():
        status = "✅ PASS" if check_result else "❌ FAIL"
        print(f"  {check_name.capitalize()}: {status}")

    print()

    if all(results.values()):
        print("✅ All checks passed! BIFX is ready to use.")
        print("\nNext step: Run the pipeline")
        print("  python run_pipeline.py")
        return 0
    else:
        print("❌ Some checks failed. Please review the errors above.")
        print("\nTo fix:")
        print("  1. Install dependencies: python setup.py")
        print("  2. Ensure all files are present")
        print("  3. Run this verification again: python verify.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
