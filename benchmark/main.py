from adapters.sps_webapi import SpsWebApiAdapter
from benchmark_runner import BenchmarkRunner

def main():
    """Main benchmark execution"""
    print("SPS API Benchmark Tool")
    print("="*60)
    
    adapter = SpsWebApiAdapter()
    adapter.connect()
    runner = BenchmarkRunner(adapter)
    
    try:
        # Test 1: Single writes
        print("\nStarting Single Write Benchmarks...")
        runner.benchmark_single_writes(target_ops_per_sec=1, duration_seconds=10)
        runner.benchmark_single_writes(target_ops_per_sec=5, duration_seconds=10)
        runner.benchmark_single_writes(target_ops_per_sec=10, duration_seconds=10)

        # Test 2: Bulk writes
        print("\nStarting Bulk Write Benchmark...")
        runner.benchmark_bulk_writes(repetitions=10)

        # Summary & Reports
        runner.print_summary()
        runner.export_results_json("results/benchmark_results.json")
        runner.save_results_report("results")

    except Exception as e:
        print(f"\nBenchmark failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nDisconnecting...")
        adapter.disconnect()
        print("✓ Done")

if __name__ == "__main__":
    main()
