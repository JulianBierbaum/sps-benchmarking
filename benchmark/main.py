from adapters.webapi import SpsWebApiAdapter
from adapters.opcua import OpcUaAdapter
from benchmark_runner import BenchmarkRunner
from datetime import datetime
import os

def run_benchmark_for_adapter(adapter_name: str, adapter, output_dir: str):
    """Run benchmarks for a single adapter and save results"""
    print(f"\n{'='*60}")
    print(f"BENCHMARKING: {adapter_name}")
    print(f"{'='*60}")
    
    try:
        adapter.connect()
        runner = BenchmarkRunner(adapter)
        
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
        
        # Create adapter-specific output directory
        adapter_output = os.path.join(output_dir, adapter_name.lower().replace(" ", "_"))
        runner.export_results_json(os.path.join(adapter_output, "benchmark_results.json"))
        runner.save_results_report(adapter_output)
        
        return runner.results
        
    except Exception as e:
        print(f"\n✗ Benchmark failed for {adapter_name}: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        print(f"\nDisconnecting {adapter_name}...")
        adapter.disconnect()


def generate_comparison_report(webapi_results, opcua_results, output_dir: str):
    """Generate a comparison report between WebAPI and OPC UA"""
    if not webapi_results or not opcua_results:
        print("\n⚠ Cannot generate comparison - missing results")
        return
    
    report_path = os.path.join(output_dir, "protocol_comparison.txt")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("PROTOCOL COMPARISON REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write("WebAPI vs OPC UA Performance Comparison\n")
        f.write("-" * 80 + "\n\n")
        
        # Match tests by name pattern
        for webapi_result in webapi_results:
            # Find matching OPC UA result
            matching_opcua = None
            for opcua_result in opcua_results:
                if opcua_result.test_name == webapi_result.test_name:
                    matching_opcua = opcua_result
                    break
            
            if matching_opcua:
                f.write(f"Test: {webapi_result.test_name}\n")
                f.write("-" * 80 + "\n")
                
                f.write(f"{'Metric':<30} {'WebAPI':<20} {'OPC UA':<20} {'Winner':<10}\n")
                f.write("-" * 80 + "\n")
                
                # Operations per second
                webapi_ops = webapi_result.ops_per_second
                opcua_ops = matching_opcua.ops_per_second
                winner_ops = "WebAPI" if webapi_ops > opcua_ops else "OPC UA"
                f.write(f"{'Ops/sec':<30} {webapi_ops:<20.2f} {opcua_ops:<20.2f} {winner_ops:<10}\n")
                
                # Latency P50
                webapi_p50 = webapi_result.latency_p50_ms
                opcua_p50 = matching_opcua.latency_p50_ms
                winner_p50 = "WebAPI" if webapi_p50 < opcua_p50 else "OPC UA"
                f.write(f"{'Latency P50 (ms)':<30} {webapi_p50:<20.2f} {opcua_p50:<20.2f} {winner_p50:<10}\n")
                
                # Latency P90
                webapi_p90 = webapi_result.latency_p90_ms
                opcua_p90 = matching_opcua.latency_p90_ms
                winner_p90 = "WebAPI" if webapi_p90 < opcua_p90 else "OPC UA"
                f.write(f"{'Latency P90 (ms)':<30} {webapi_p90:<20.2f} {opcua_p90:<20.2f} {winner_p90:<10}\n")
                
                # Latency P99
                webapi_p99 = webapi_result.latency_p99_ms
                opcua_p99 = matching_opcua.latency_p99_ms
                winner_p99 = "WebAPI" if webapi_p99 < opcua_p99 else "OPC UA"
                f.write(f"{'Latency P99 (ms)':<30} {webapi_p99:<20.2f} {opcua_p99:<20.2f} {winner_p99:<10}\n")
                
                # Throughput (if applicable)
                if webapi_result.throughput_kbps > 0:
                    webapi_tp = webapi_result.throughput_kbps
                    opcua_tp = matching_opcua.throughput_kbps
                    winner_tp = "WebAPI" if webapi_tp > opcua_tp else "OPC UA"
                    f.write(f"{'Throughput (kB/s)':<30} {webapi_tp:<20.2f} {opcua_tp:<20.2f} {winner_tp:<10}\n")
                
                # Performance difference
                perf_diff = ((webapi_ops - opcua_ops) / opcua_ops) * 100
                if perf_diff > 0:
                    f.write(f"\n→ WebAPI is {perf_diff:.1f}% faster\n")
                else:
                    f.write(f"\n→ OPC UA is {abs(perf_diff):.1f}% faster\n")
                
                f.write("\n" + "=" * 80 + "\n\n")
    
    print(f"\n✓ Comparison report saved: {report_path}")
    
    # Also print to console
    print(f"\n{'='*80}")
    print("QUICK COMPARISON SUMMARY")
    print(f"{'='*80}")
    for webapi_result in webapi_results:
        matching_opcua = next((r for r in opcua_results if r.test_name == webapi_result.test_name), None)
        if matching_opcua:
            faster = "WebAPI" if webapi_result.ops_per_second > matching_opcua.ops_per_second else "OPC UA"
            diff = abs(((webapi_result.ops_per_second - matching_opcua.ops_per_second) / 
                       matching_opcua.ops_per_second) * 100)
            print(f"{webapi_result.test_name:30} | Winner: {faster:8} ({diff:.1f}% faster)")
    print(f"{'='*80}\n")


def main():
    """Main benchmark execution for multiple protocols"""
    print("SPS Multi-Protocol Benchmark Tool")
    print("="*60)
    print("Testing: WebAPI and OPC UA\n")
    
    output_dir = "results_" + datetime.now().strftime("%Y%m%d_%H%M%S") 
    os.makedirs(output_dir, exist_ok=True)
    
    # Benchmark WebAPI
    webapi_adapter = SpsWebApiAdapter()
    webapi_results = run_benchmark_for_adapter("WebAPI", webapi_adapter, output_dir)
    
    print("\n" + "="*60)
    print("Pausing 2 seconds between protocols...")
    print("="*60)
    import time
    time.sleep(2)
    
    # Benchmark OPC UA
    opcua_adapter = OpcUaAdapter()
    opcua_results = run_benchmark_for_adapter("OPC UA", opcua_adapter, output_dir)
    
    # Generate comparison report
    if webapi_results and opcua_results:
        generate_comparison_report(webapi_results, opcua_results, output_dir)
    
    print("\n" + "="*60)
    print("✓ All benchmarks completed!")
    print(f"✓ Results saved in '{output_dir}/' directory")
    print("  - webapi/")
    print("  - opcua/")
    print("  - protocol_comparison.txt")
    print("="*60)


if __name__ == "__main__":
    main()