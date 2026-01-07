from adapters.webapi import SpsWebApiAdapter
from adapters.opcua import OpcUaAdapter
from adapters.s7 import S7Adapter
from benchmark_runner import BenchmarkRunner
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import os


def run_benchmark_for_adapter(adapter_name: str, adapter, output_dir: str):
    """Run benchmarks for a single adapter and save results"""
    print(f"\n{'=' * 60}")
    print(f"BENCHMARKING: {adapter_name}")
    print(f"{'=' * 60}")

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
        adapter_output = os.path.join(
            output_dir, adapter_name.lower().replace(" ", "_")
        )
        runner.export_results_json(
            os.path.join(adapter_output, "benchmark_results.json")
        )
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


def generate_comparison_plots(all_results: list, output_dir: str):
    """Generate combined comparison plots for all protocols.

    Args:
        all_results: List of tuples (protocol_name, results_list)
        output_dir: Directory to save the plots
    """
    # Filter out protocols with no results
    valid_results = [(name, results) for name, results in all_results if results]

    if len(valid_results) < 2:
        print("\n⚠ Cannot generate comparison plots - need at least 2 protocols")
        return

    colors = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12"]  # Blue, Red, Green, Orange

    # Get all unique test names from first protocol
    test_names = [r.test_name for r in valid_results[0][1]]

    # --- Plot 1: Latency P50 Comparison (Log Scale) ---
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(test_names))
    width = 0.25

    all_latencies = []
    for i, (proto_name, results) in enumerate(valid_results):
        latencies = []
        for test_name in test_names:
            match = next((r for r in results if r.test_name == test_name), None)
            lat = (
                match.latency_p50_ms if match and match.latency_p50_ms > 0 else 0.1
            )  # Avoid log(0)
            latencies.append(lat)
            all_latencies.append(lat)

        offset = (i - len(valid_results) / 2 + 0.5) * width
        bars = ax.bar(
            x + offset,
            latencies,
            width,
            label=proto_name,
            color=colors[i % len(colors)],
        )

        # Add value labels on bars
        for bar, val in zip(bars, latencies):
            if val > 0.1:
                ax.annotate(
                    f"{val:.1f}",
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    rotation=45,
                )

    ax.set_xlabel("Benchmark Test")
    ax.set_ylabel("Latency P50 (ms)")
    ax.set_title("Latency Comparison (P50) - Lower is Better")
    ax.set_xticks(x)
    ax.set_xticklabels([t.replace("_", "\n") for t in test_names], fontsize=9)
    ax.set_yscale("log")  # Use log scale for better visibility
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "comparison_latency.png"), dpi=150)
    plt.close()

    # --- Plot 2: Operations Per Second Comparison (Log Scale) ---
    fig, ax = plt.subplots(figsize=(12, 6))

    for i, (proto_name, results) in enumerate(valid_results):
        ops_list = []
        for test_name in test_names:
            match = next((r for r in results if r.test_name == test_name), None)
            ops = match.ops_per_second if match and match.ops_per_second > 0 else 0.1
            ops_list.append(ops)

        offset = (i - len(valid_results) / 2 + 0.5) * width
        bars = ax.bar(
            x + offset, ops_list, width, label=proto_name, color=colors[i % len(colors)]
        )

        # Add value labels on bars
        for bar, val in zip(bars, ops_list):
            if val > 0.1:
                ax.annotate(
                    f"{val:.1f}",
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    rotation=45,
                )

    ax.set_xlabel("Benchmark Test")
    ax.set_ylabel("Operations per Second")
    ax.set_title("Throughput Comparison - Higher is Better")
    ax.set_xticks(x)
    ax.set_xticklabels([t.replace("_", "\n") for t in test_names], fontsize=9)
    ax.set_yscale("log")  # Use log scale for better visibility
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "comparison_ops.png"), dpi=150)
    plt.close()

    print("✓ Comparison plots saved: comparison_latency.png, comparison_ops.png")


def generate_comparison_report(all_results: list, output_dir: str):
    """Generate a comparison report between all protocols.

    Args:
        all_results: List of tuples (protocol_name, results_list)
        output_dir: Directory to save the report
    """
    # Filter out protocols with no results
    valid_results = [(name, results) for name, results in all_results if results]

    if len(valid_results) < 2:
        print("\n⚠ Cannot generate comparison - need at least 2 protocols with results")
        return

    report_path = os.path.join(output_dir, "protocol_comparison.txt")
    protocol_names = [name for name, _ in valid_results]

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("PROTOCOL COMPARISON REPORT\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Protocols Tested: {', '.join(protocol_names)}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("-" * 100 + "\n\n")

        # Get all unique test names from first protocol
        first_protocol_results = valid_results[0][1]

        for test_result in first_protocol_results:
            test_name = test_result.test_name

            # Collect matching results from all protocols
            matching_results = []
            for proto_name, proto_results in valid_results:
                match = next(
                    (r for r in proto_results if r.test_name == test_name), None
                )
                if match:
                    matching_results.append((proto_name, match))

            if len(matching_results) < 2:
                continue

            f.write(f"Test: {test_name}\n")
            f.write("-" * 100 + "\n")

            # Build dynamic header based on protocols
            header = f"{'Metric':<25}"
            for proto_name, _ in matching_results:
                header += f" {proto_name:<15}"
            header += f" {'Winner':<10}\n"
            f.write(header)
            f.write("-" * 100 + "\n")

            # Operations per second (higher is better)
            ops_values = [(name, r.ops_per_second) for name, r in matching_results]
            winner_ops = max(ops_values, key=lambda x: x[1])[0]
            line = f"{'Ops/sec':<25}"
            for _, r in matching_results:
                line += f" {r.ops_per_second:<15.2f}"
            line += f" {winner_ops:<10}\n"
            f.write(line)

            # Latency P50 (lower is better)
            p50_values = [(name, r.latency_p50_ms) for name, r in matching_results]
            # Filter out zero values when determining winner
            non_zero_p50 = [(n, v) for n, v in p50_values if v > 0]
            winner_p50 = (
                min(non_zero_p50, key=lambda x: x[1])[0] if non_zero_p50 else "N/A"
            )
            line = f"{'Latency P50 (ms)':<25}"
            for _, r in matching_results:
                line += f" {r.latency_p50_ms:<15.2f}"
            line += f" {winner_p50:<10}\n"
            f.write(line)

            # Latency P90 (lower is better)
            p90_values = [(name, r.latency_p90_ms) for name, r in matching_results]
            non_zero_p90 = [(n, v) for n, v in p90_values if v > 0]
            winner_p90 = (
                min(non_zero_p90, key=lambda x: x[1])[0] if non_zero_p90 else "N/A"
            )
            line = f"{'Latency P90 (ms)':<25}"
            for _, r in matching_results:
                line += f" {r.latency_p90_ms:<15.2f}"
            line += f" {winner_p90:<10}\n"
            f.write(line)

            # Latency P99 (lower is better)
            p99_values = [(name, r.latency_p99_ms) for name, r in matching_results]
            non_zero_p99 = [(n, v) for n, v in p99_values if v > 0]
            winner_p99 = (
                min(non_zero_p99, key=lambda x: x[1])[0] if non_zero_p99 else "N/A"
            )
            line = f"{'Latency P99 (ms)':<25}"
            for _, r in matching_results:
                line += f" {r.latency_p99_ms:<15.2f}"
            line += f" {winner_p99:<10}\n"
            f.write(line)

            # Throughput (higher is better, if applicable)
            if any(r.throughput_kbps > 0 for _, r in matching_results):
                tp_values = [(name, r.throughput_kbps) for name, r in matching_results]
                winner_tp = max(tp_values, key=lambda x: x[1])[0]
                line = f"{'Throughput (kB/s)':<25}"
                for _, r in matching_results:
                    line += f" {r.throughput_kbps:<15.2f}"
                line += f" {winner_tp:<10}\n"
                f.write(line)

            # Overall winner by ops/sec
            f.write(
                f"\n→ Fastest: {winner_ops} ({max(ops_values, key=lambda x: x[1])[1]:.2f} ops/s)\n"
            )
            f.write("\n" + "=" * 100 + "\n\n")

    print(f"\n✓ Comparison report saved: {report_path}")

    # Also print to console
    print(f"\n{'=' * 100}")
    print("QUICK COMPARISON SUMMARY")
    print(f"{'=' * 100}")

    for test_result in first_protocol_results:
        test_name = test_result.test_name
        ops_by_proto = []
        for proto_name, proto_results in valid_results:
            match = next((r for r in proto_results if r.test_name == test_name), None)
            if match:
                ops_by_proto.append((proto_name, match.ops_per_second))

        if len(ops_by_proto) >= 2:
            winner = max(ops_by_proto, key=lambda x: x[1])
            print(f"{test_name:30} | Winner: {winner[0]:8} ({winner[1]:.2f} ops/s)")

    print(f"{'=' * 100}\n")


def main():
    """Main benchmark execution for multiple protocols"""
    print("SPS Multi-Protocol Benchmark Tool")
    print("=" * 60)
    print("Testing: WebAPI, OPC UA, and S7\n")

    output_dir = "results_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(output_dir, exist_ok=True)

    # Benchmark WebAPI
    webapi_adapter = SpsWebApiAdapter()
    webapi_results = run_benchmark_for_adapter("WebAPI", webapi_adapter, output_dir)

    print("\n" + "=" * 60)
    print("Pausing 2 seconds between protocols...")
    print("=" * 60)
    import time

    time.sleep(2)

    # Benchmark OPC UA
    opcua_adapter = OpcUaAdapter()
    opcua_results = run_benchmark_for_adapter("OPC UA", opcua_adapter, output_dir)

    print("\n" + "=" * 60)
    print("Pausing 2 seconds between protocols...")
    print("=" * 60)
    time.sleep(2)

    # Benchmark S7
    s7_adapter = S7Adapter()
    s7_results = run_benchmark_for_adapter("S7", s7_adapter, output_dir)

    # Generate comparison report with all protocols
    all_results = [
        ("WebAPI", webapi_results),
        ("OPC UA", opcua_results),
        ("S7", s7_results),
    ]

    generate_comparison_report(all_results, output_dir)
    generate_comparison_plots(all_results, output_dir)

    print("\n" + "=" * 60)
    print("✓ All benchmarks completed!")
    print(f"✓ Results saved in '{output_dir}/' directory")
    print("  - webapi/")
    print("  - opc_ua/")
    print("  - s7/")
    print("  - protocol_comparison.txt")
    print("  - comparison_latency.png")
    print("  - comparison_ops.png")
    print("=" * 60)


if __name__ == "__main__":
    main()
