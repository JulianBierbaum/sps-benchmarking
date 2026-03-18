# SPS Benchmarking Suite

A performance testing suite designed to evaluate and compare communication protocols when interacting with a Siemens S7.

## Overview

The suite measures latency and throughput for three different communication protocols:

| Protocol | Library |
|----------|---------|
| **OPC UA** | `opcua` |
| **Siemens Web API** | `requests` |
| **S7 (Proprietary)** | `python-snap7` |

### Benchmarks Included
- **Single Writes:** Repeatedly writing individual variables (Bool, Int16, Int32) at configurable rates (e.g., 20 Ops/s).
- **Bulk Writes:** Transferring a data block of approximately 1 kB (100 × LTime values).

---

## Prerequisites

1. **Python 3.12+**
2. **[uv](https://github.com/astral-sh/uv)** (Python package manager)
3. **Siemens S7 PLC** accessible via network.
4. **Configuration:** Connection parameters and protocol settings defined in a `.env` file (see `.env.example`).

---

## Installation

1. Clone the repository and navigate to the `benchmark` directory:
   ```bash
   cd benchmark
   ```

2. Sync dependencies using `uv`:
   ```bash
   uv sync
   ```

3. Set up the environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in your PLC's IP address, credentials, and protocol-specific details (e.g., OPC UA endpoint, S7 Rack/Slot).

---

## Usage

Run the main benchmarking script:
```bash
uv run python main.py
```

### Output
The results are stored in a timestamped directory `results_YYYYMMDD_HHMMSS/`:
- `protocol_comparison.txt`: Tabular summary of all protocol results.
- `comparison_latency.png`: Latency comparison chart (P50, P90, P99).
- `comparison_ops.png`: Throughput comparison chart (Ops/s).
- Individual subdirectories for each protocol containing detailed logs and plots.

---

## Architecture

The project utilizes the Adapter-Pattern to decouple benchmarking logic from protocol-specific implementations. 
This allows for consistency across all protocols and easy extensibility.

- `adapters/base.py`: Abstract Base Class for all adapters.
- `adapters/webapi.py`: Implementation for Siemens Web API.
- `adapters/opcua.py`: Implementation for OPC UA.
- `adapters/s7.py`: Implementation for the S7 proprietary protocol.

---

## Key Metrics Measured
- **Ops/s:** Operations per second (achieved rate).
- **Latency (P50/P90/P99):** Percentile distribution of response times.
- **Throughput (kB/s):** Data transfer speed for bulk operations.
