from adapters.base import ProtocolAdapter
from dataclasses import dataclass, asdict
import json
import time
import statistics
from dataclasses import dataclass, asdict
import os
from datetime import datetime
import matplotlib.pyplot as plt

@dataclass
class BenchmarkResult:
    """Store benchmark results"""
    test_name: str
    total_operations: int
    duration_seconds: float
    ops_per_second: float
    latency_p50_ms: float
    latency_p90_ms: float
    latency_p99_ms: float
    throughput_kbps: float = 0.0
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class BenchmarkRunner:
    def __init__(self, adapter: ProtocolAdapter):
        self.api = adapter
        self.results = []

    def benchmark_single_writes(self, target_ops_per_sec: int, 
                               duration_seconds: int = 10) -> BenchmarkResult:
        """
        Benchmark individual write operations at specified rate
        
        Args:
            target_ops_per_sec: Target operations per second
            duration_seconds: How long to run the test
        """
        print(f"\n{'='*60}")
        print(f"Single Write Benchmark: {target_ops_per_sec} ops/s for {duration_seconds}s")
        print(f"{'='*60}")
        
        latencies = []
        operations = 0
        interval = 1.0 / target_ops_per_sec  # Time between operations
        
        start_time = time.time()
        next_op_time = start_time
        
        try:
            while (time.time() - start_time) < duration_seconds:
                # Wait until next operation time
                current_time = time.time()
                if current_time < next_op_time:
                    time.sleep(next_op_time - current_time)
                
                # Perform write operation (toggle a boolean value)
                value = operations % 2 == 0  # Alternate True/False
                try:
                    _, latency = self.api.write(
                        '"PerformaceData".ToServer.bool00', 
                        value
                    )
                    latencies.append(latency)
                    operations += 1
                except Exception as e:
                    print(f"✗ Write failed: {e}")
                
                next_op_time += interval
                
        except KeyboardInterrupt:
            print("\n⚠ Benchmark interrupted by user")
        
        total_duration = time.time() - start_time
        
        # Calculate statistics
        if latencies:
            latencies.sort()
            p50 = statistics.median(latencies)
            p90 = latencies[int(len(latencies) * 0.90)]
            p99 = latencies[int(len(latencies) * 0.99)]
            actual_ops = operations / total_duration
        else:
            p50 = p90 = p99 = actual_ops = 0
        
        result = BenchmarkResult(
            test_name=f"Single_Write_{target_ops_per_sec}ops",
            total_operations=operations,
            duration_seconds=total_duration,
            ops_per_second=actual_ops,
            latency_p50_ms=p50,
            latency_p90_ms=p90,
            latency_p99_ms=p99
        )
        
        self.results.append(result)
        self._print_result(result)
        return result

    def benchmark_bulk_writes(self, repetitions: int = 10) -> BenchmarkResult:
        """
        Benchmark bulk data writes (entire BulkData array)
        
        Args:
            repetitions: Number of times to repeat the bulk write
        """
        print(f"\n{'='*60}")
        print(f"Bulk Write Benchmark: {repetitions} repetitions")
        print(f"{'='*60}")
        
        # Generate test data for BulkData[0..999]
        # Using LTime format: LT#<value>ns
        bulk_data = [f"LT#{i * 1000000}ns" for i in range(1000)]
        data_size_bytes = len(json.dumps(bulk_data))
        
        latencies = []
        
        start_time = time.time()
        
        for i in range(repetitions):
            try:
                _, latency = self.api.write_bulk_data(bulk_data)
                latencies.append(latency)
                print(f"  Repetition {i+1}/{repetitions}: {latency:.2f} ms")
            except Exception as e:
                print(f"✗ Bulk write {i+1} failed: {e}")
        
        total_duration = time.time() - start_time
        
        # Calculate statistics
        if latencies:
            latencies.sort()
            p50 = statistics.median(latencies)
            p90 = latencies[int(len(latencies) * 0.90)] if len(latencies) > 1 else p50
            p99 = latencies[int(len(latencies) * 0.99)] if len(latencies) > 1 else p50
            
            # Calculate throughput in kB/s
            total_data_kb = (data_size_bytes * repetitions) / 1024
            throughput_kbps = total_data_kb / total_duration
        else:
            p50 = p90 = p99 = throughput_kbps = 0
        
        result = BenchmarkResult(
            test_name=f"Bulk_Write_1000_elements",
            total_operations=repetitions,
            duration_seconds=total_duration,
            ops_per_second=repetitions / total_duration,
            latency_p50_ms=p50,
            latency_p90_ms=p90,
            latency_p99_ms=p99,
            throughput_kbps=throughput_kbps
        )
        
        self.results.append(result)
        self._print_result(result)
        return result

    def save_results_report(self, output_dir: str = "results"):
        """Generate plots and a text report of benchmark results"""
        os.makedirs(output_dir, exist_ok=True)
        
        # --- Generate plots ---
        test_names = [r.test_name for r in self.results]
        lat_p50 = [r.latency_p50_ms for r in self.results]
        lat_p90 = [r.latency_p90_ms for r in self.results]
        lat_p99 = [r.latency_p99_ms for r in self.results]
        ops_per_sec = [r.ops_per_second for r in self.results]

        # Plot: Latency comparison
        plt.figure(figsize=(8, 5))
        plt.plot(test_names, lat_p50, marker='o', label='P50')
        plt.plot(test_names, lat_p90, marker='o', label='P90')
        plt.plot(test_names, lat_p99, marker='o', label='P99')
        plt.title("Latency Percentiles (ms)")
        plt.ylabel("Latency (ms)")
        plt.xlabel("Benchmark Test")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "latency_plot.png"))
        plt.close()

        # Plot: Operations per second
        plt.figure(figsize=(8, 5))
        plt.bar(test_names, ops_per_sec, color='skyblue')
        plt.title("Operations per Second")
        plt.ylabel("Ops/s")
        plt.xlabel("Benchmark Test")
        plt.grid(True, axis='y')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "ops_per_sec.png"))
        plt.close()

        # --- Generate text report ---
        report_path = os.path.join(output_dir, "benchmark_report.txt")
        with open(report_path, "w") as f:
            f.write("SPS API BENCHMARK REPORT\n")
            f.write("=" * 60 + "\n\n")
            for r in self.results:
                f.write(f"Test: {r.test_name}\n")
                f.write(f"  Operations:   {r.total_operations}\n")
                f.write(f"  Duration:     {r.duration_seconds:.2f} s\n")
                f.write(f"  Ops/sec:      {r.ops_per_second:.2f}\n")
                f.write(f"  Latency P50:  {r.latency_p50_ms:.2f} ms\n")
                f.write(f"  Latency P90:  {r.latency_p90_ms:.2f} ms\n")
                f.write(f"  Latency P99:  {r.latency_p99_ms:.2f} ms\n")
                if r.throughput_kbps > 0:
                    f.write(f"  Throughput:   {r.throughput_kbps:.2f} kB/s\n")
                f.write(f"  Timestamp:    {r.timestamp}\n")
                f.write("-" * 60 + "\n")
            f.write("\nPlots saved in: results/\n")

        print(f"\n✓ Report and plots saved in '{output_dir}/'")

    def _print_result(self, result: BenchmarkResult):
        """Pretty print benchmark result"""
        print(f"\n{'─'*60}")
        print(f"Results for {result.test_name}")
        print(f"{'─'*60}")
        print(f"  Operations:        {result.total_operations}")
        print(f"  Duration:          {result.duration_seconds:.2f} s")
        print(f"  Actual Rate:       {result.ops_per_second:.2f} ops/s")
        print(f"  Latency P50:       {result.latency_p50_ms:.2f} ms")
        print(f"  Latency P90:       {result.latency_p90_ms:.2f} ms")
        print(f"  Latency P99:       {result.latency_p99_ms:.2f} ms")
        if result.throughput_kbps > 0:
            print(f"  Throughput:        {result.throughput_kbps:.2f} kB/s")
        print(f"{'─'*60}")

    def print_summary(self):
        """Print summary of all benchmark results"""
        print(f"\n{'='*60}")
        print("BENCHMARK SUMMARY")
        print(f"{'='*60}\n")
        
        for result in self.results:
            print(f"{result.test_name:30} | "
                  f"Rate: {result.ops_per_second:8.2f} ops/s | "
                  f"P50: {result.latency_p50_ms:7.2f} ms | "
                  f"P99: {result.latency_p99_ms:7.2f} ms")
        
        print(f"\n{'='*60}")

    def export_results_json(self, filename: str = "benchmark_results.json"):
        """Export results to JSON file"""
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        with open(filename, 'w') as f:
            json.dump([asdict(r) for r in self.results], f, indent=2)
        print(f"\n✓ Results exported to {filename}")

