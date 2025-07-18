#!/usr/bin/env python
"""
DPA'�K��L,

�Lhb�'���K��
1. API͔���K�
2. pn��\'�K�
3. }���K�
4. AI!�'���K�
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime
from pathlib import Path

# ��y�9�U0Python�
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.performance import (
    test_core_endpoints,
    run_load_tests,
    run_database_benchmarks,
    run_model_performance_tests
)


async def run_api_tests():
    """�LAPI'�K�"""
    print("\n" + "="*60)
    print(" �API'�K�")
    print("="*60)
    
    try:
        await test_core_endpoints()
        print("\n API'�KՌ")
    except Exception as e:
        print(f"\nL API'�K�1%: {e}")
        return False
    return True


async def run_database_tests():
    """�Lpn�'�K�"""
    print("\n" + "="*60)
    print(" �pn�'�K�")
    print("="*60)
    
    try:
        await run_database_benchmarks()
        print("\n pn�'�KՌ")
    except Exception as e:
        print(f"\nL pn�'�K�1%: {e}")
        return False
    return True


async def run_load_test():
    """�L}K�"""
    print("\n" + "="*60)
    print(" �}K�")
    print("="*60)
    
    try:
        await run_load_tests()
        print("\n }KՌ")
    except Exception as e:
        print(f"\nL }K�1%: {e}")
        return False
    return True


async def run_model_tests():
    """�LAI!�'�K�"""
    print("\n" + "="*60)
    print(" �AI!�'�K�")
    print("="*60)
    
    try:
        await run_model_performance_tests()
        print("\n AI!�'�KՌ")
    except Exception as e:
        print(f"\nL AI!�'�K�1%: {e}")
        return False
    return True


async def run_all_tests():
    """�L@	'�K�"""
    print(f"\nDPA'���K�W�")
    print(f" ���: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {
        "APIK�": False,
        "pn�K�": False,
        "}K�": False,
        "!�K�": False
    }
    
    # �LyK�
    if not args.skip_api:
        results["APIK�"] = await run_api_tests()
    
    if not args.skip_database:
        results["pn�K�"] = await run_database_tests()
    
    if not args.skip_load:
        results["}K�"] = await run_load_test()
    
    if not args.skip_model:
        results["!�K�"] = await run_model_tests()
    
    # ;ӥJ
    print("\n" + "="*60)
    print("'�K�;�")
    print("="*60)
    
    for test_name, success in results.items():
        status = " �" if success else "L 1%"
        print(f"{test_name}: {status}")
    
    # ��/&@	K���
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    print(f"���: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if all_passed:
        print("<� @	'�K��")
        return 0
    else:
        print("�  �'�K�1%�����")
        return 1


def parse_arguments():
    """�}�L�p"""
    parser = argparse.ArgumentParser(
        description="DPA'�K��Lh",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
:�:
  # �L@	K�
  python run_performance_tests.py
  
  # ��LAPIK�
  python run_performance_tests.py --only api
  
  # ��pn�K�
  python run_performance_tests.py --skip-database
  
  # �L�K����	
  python run_performance_tests.py --quick
        """
    )
    
    # K�	�
    parser.add_argument(
        "--only",
        choices=["api", "database", "load", "model"],
        help="��L��K�"
    )
    
    parser.add_argument(
        "--skip-api",
        action="store_true",
        help="��API'�K�"
    )
    
    parser.add_argument(
        "--skip-database",
        action="store_true",
        help="��pn�'�K�"
    )
    
    parser.add_argument(
        "--skip-load",
        action="store_true",
        help="��}K�"
    )
    
    parser.add_argument(
        "--skip-model",
        action="store_true",
        help="��AI!�K�"
    )
    
    # K�Mn
    parser.add_argument(
        "--quick",
        action="store_true",
        help="�!�K���!p	"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./performance_results",
        help="K�Ӝ���U"
    )
    
    return parser.parse_args()


async def run_single_test(test_type: str):
    """�LU*K�"""
    test_map = {
        "api": run_api_tests,
        "database": run_database_tests,
        "load": run_load_test,
        "model": run_model_tests
    }
    
    if test_type in test_map:
        success = await test_map[test_type]()
        return 0 if success else 1
    else:
        print(f"*�K�{�: {test_type}")
        return 1


if __name__ == "__main__":
    # ��p
    args = parse_arguments()
    
    # �n����
    if args.quick:
        os.environ["PERF_TEST_QUICK_MODE"] = "1"
    
    # ����U
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(output_dir)
    
    # �LK�
    if args.only:
        exit_code = asyncio.run(run_single_test(args.only))
    else:
        exit_code = asyncio.run(run_all_tests())
    
    sys.exit(exit_code)