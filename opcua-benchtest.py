"""
OPC UA Performance Benchmark für Siemens S7-1500 PLC
Testet hochfrequentes Schreiben einzelner Variablen und Bulk-Datenübertragung
"""

from opcua import Client, ua    
import time
import statistics
import json
from datetime import datetime
from typing import List, Dict
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OPCUABenchmark:
    def __init__(self, server_url: str = "opc.tcp://192.168.10.61:4840"):
        """
        Initialisiert die OPC UA Benchmark-Klasse
        
        Args:
            server_url: OPC UA Server URL
        """
        self.server_url = server_url
        self.client = None
        self.results = {
            "protocol": "OPC UA",
            "server": server_url,
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
    def connect(self):
        """Verbindung zum OPC UA Server herstellen"""
        try:
            self.client = Client(self.server_url)
            self.client.connect()
            logger.info(f"Verbunden mit OPC UA Server: {self.server_url}")
            return True
        except Exception as e:
            logger.error(f"Verbindungsfehler: {e}")
            return False
    
    def disconnect(self):
        """Verbindung trennen"""
        if self.client:
            self.client.disconnect()
            logger.info("Verbindung getrennt")
    
    def get_node(self, node_id: str):
        """
        Holt einen OPC UA Node
        
        Args:
            node_id: Node Identifier (z.B. "ns=3;s=\"PerformaceData\".ToServer.bool00")
        """
        try:
            return self.client.get_node(node_id)
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Nodes {node_id}: {e}")
            return None
    
    def benchmark_single_bool_write(self, iterations: int = 1000) -> Dict:
        """
        Benchmark für hochfrequentes Schreiben einzelner Bool-Variablen
        
        Args:
            iterations: Anzahl der Schreibvorgänge
        """
        logger.info(f"Starte Bool Write Test ({iterations} Iterationen)...")
        
        node = self.get_node('ns=3;s="PerformaceData".ToServer.bool00')
        if not node:
            return {"error": "Node nicht gefunden"}
        
        times = []
        errors = 0
        value = False
        
        for i in range(iterations):
            try:
                start = time.perf_counter()
                node.set_value(ua.DataValue(ua.Variant(value, ua.VariantType.Boolean)))
                end = time.perf_counter()
                times.append((end - start) * 1000)  # in ms
                value = not value  # Toggle
            except Exception as e:
                errors += 1
                logger.warning(f"Fehler bei Iteration {i}: {e}")
        
        result = self._calculate_statistics(times, "Bool Write", iterations, errors)
        self.results["tests"]["bool_write"] = result
        return result
    
    def benchmark_single_int16_write(self, iterations: int = 1000) -> Dict:
        """
        Benchmark für hochfrequentes Schreiben einzelner Int16-Variablen
        
        Args:
            iterations: Anzahl der Schreibvorgänge
        """
        logger.info(f"Starte Int16 Write Test ({iterations} Iterationen)...")
        
        node = self.get_node('ns=3;s="PerformaceData".ToServer.int16_01')
        if not node:
            return {"error": "Node nicht gefunden"}
        
        times = []
        errors = 0
        
        for i in range(iterations):
            try:
                start = time.perf_counter()
                node.set_value(ua.DataValue(ua.Variant(i % 32767, ua.VariantType.Int16)))
                end = time.perf_counter()
                times.append((end - start) * 1000)
            except Exception as e:
                errors += 1
                logger.warning(f"Fehler bei Iteration {i}: {e}")
        
        result = self._calculate_statistics(times, "Int16 Write", iterations, errors)
        self.results["tests"]["int16_write"] = result
        return result
    
    def benchmark_single_int32_write(self, iterations: int = 1000) -> Dict:
        """
        Benchmark für hochfrequentes Schreiben einzelner Int32-Variablen
        
        Args:
            iterations: Anzahl der Schreibvorgänge
        """
        logger.info(f"Starte Int32 Write Test ({iterations} Iterationen)...")
        
        node = self.get_node('ns=3;s="PerformaceData".ToServer.int32_01')
        if not node:
            return {"error": "Node nicht gefunden"}
        
        times = []
        errors = 0
        
        for i in range(iterations):
            try:
                start = time.perf_counter()
                node.set_value(ua.DataValue(ua.Variant(i, ua.VariantType.Int32)))
                end = time.perf_counter()
                times.append((end - start) * 1000)
            except Exception as e:
                errors += 1
                logger.warning(f"Fehler bei Iteration {i}: {e}")
        
        result = self._calculate_statistics(times, "Int32 Write", iterations, errors)
        self.results["tests"]["int32_write"] = result
        return result
    
    def benchmark_bulk_data_write(self, iterations: int = 100) -> Dict:
        """
        Benchmark für Übertragung größerer Datenmengen (~1 kByte)
        Schreibt in das BulkData Array (900 LTime Werte = 7200 Bytes)
        
        Args:
            iterations: Anzahl der Schreibvorgänge
        """
        logger.info(f"Starte Bulk Data Write Test ({iterations} Iterationen)...")
        
        # Array mit 100 LTime Werten (~800 Bytes)
        times = []
        errors = 0
        
        for i in range(iterations):
            try:
                nodes_to_write = []
                values_to_write = []
                
                # Schreibe 100 aufeinanderfolgende Array-Elemente
                for j in range(100):
                    node = self.get_node(f'ns=3;s="PerformaceData".PlcData.BulkData[{j}]')
                    if node:
                        nodes_to_write.append(node)
                        # LTime Wert in Nanosekunden
                        values_to_write.append(ua.DataValue(ua.Variant(i * 1000000 + j, ua.VariantType.Int64)))
                
                start = time.perf_counter()
                # Batch-Write für bessere Performance
                for idx, node in enumerate(nodes_to_write):
                    node.set_value(values_to_write[idx])
                end = time.perf_counter()
                
                times.append((end - start) * 1000)
            except Exception as e:
                errors += 1
                logger.warning(f"Fehler bei Iteration {i}: {e}")
        
        result = self._calculate_statistics(times, "Bulk Data Write (~800 Bytes)", iterations, errors)
        self.results["tests"]["bulk_write"] = result
        return result
    
    def benchmark_bulk_data_read(self, iterations: int = 100) -> Dict:
        """
        Benchmark für Lesen größerer Datenmengen (~1 kByte)
        
        Args:
            iterations: Anzahl der Lesevorgänge
        """
        logger.info(f"Starte Bulk Data Read Test ({iterations} Iterationen)...")
        
        times = []
        errors = 0
        
        for i in range(iterations):
            try:
                nodes_to_read = []
                
                # Lese 100 aufeinanderfolgende Array-Elemente
                for j in range(100):
                    node = self.get_node(f'ns=3;s="PerformaceData".PlcData.BulkData[{j}]')
                    if node:
                        nodes_to_read.append(node)
                
                start = time.perf_counter()
                for node in nodes_to_read:
                    value = node.get_value()
                end = time.perf_counter()
                
                times.append((end - start) * 1000)
            except Exception as e:
                errors += 1
                logger.warning(f"Fehler bei Iteration {i}: {e}")
        
        result = self._calculate_statistics(times, "Bulk Data Read (~800 Bytes)", iterations, errors)
        self.results["tests"]["bulk_read"] = result
        return result
    
    def benchmark_mixed_operations(self, iterations: int = 500) -> Dict:
        """
        Benchmark mit gemischten Operationen (Read/Write verschiedener Datentypen)
        
        Args:
            iterations: Anzahl der Zyklen
        """
        logger.info(f"Starte Mixed Operations Test ({iterations} Iterationen)...")
        
        times = []
        errors = 0
        
        nodes = {
            'bool': self.get_node('ns=3;s="PerformaceData".ToServer.bool00'),
            'int16': self.get_node('ns=3;s="PerformaceData".ToServer.int16_01'),
            'int32': self.get_node('ns=3;s="PerformaceData".ToServer.int32_01'),
            'real': self.get_node('ns=3;s="PerformaceData".ToServer.Real01')
        }
        
        for i in range(iterations):
            try:
                start = time.perf_counter()
                
                # Write operations
                nodes['bool'].set_value(ua.DataValue(ua.Variant(i % 2 == 0, ua.VariantType.Boolean)))
                nodes['int16'].set_value(ua.DataValue(ua.Variant(i % 32767, ua.VariantType.Int16)))
                nodes['int32'].set_value(ua.DataValue(ua.Variant(i, ua.VariantType.Int32)))
                nodes['real'].set_value(ua.DataValue(ua.Variant(float(i) * 1.5, ua.VariantType.Float)))
                
                # Read operations
                _ = nodes['bool'].get_value()
                _ = nodes['int16'].get_value()
                
                end = time.perf_counter()
                times.append((end - start) * 1000)
            except Exception as e:
                errors += 1
                logger.warning(f"Fehler bei Iteration {i}: {e}")
        
        result = self._calculate_statistics(times, "Mixed Operations", iterations, errors)
        self.results["tests"]["mixed_operations"] = result
        return result
    
    def _calculate_statistics(self, times: List[float], test_name: str, 
                             iterations: int, errors: int) -> Dict:
        """Berechnet Statistiken aus den Messwerten"""
        if not times:
            return {
                "test": test_name,
                "error": "Keine gültigen Messwerte",
                "iterations": iterations,
                "errors": errors
            }
        
        result = {
            "test": test_name,
            "iterations": iterations,
            "successful": len(times),
            "errors": errors,
            "min_ms": round(min(times), 3),
            "max_ms": round(max(times), 3),
            "mean_ms": round(statistics.mean(times), 3),
            "median_ms": round(statistics.median(times), 3),
            "stdev_ms": round(statistics.stdev(times), 3) if len(times) > 1 else 0,
            "throughput_ops_per_sec": round(1000 / statistics.mean(times), 2) if statistics.mean(times) > 0 else 0
        }
        
        logger.info(f"{test_name} - Durchschnitt: {result['mean_ms']}ms, "
                   f"Durchsatz: {result['throughput_ops_per_sec']} ops/s")
        
        return result
    
    def run_all_benchmarks(self):
        """Führt alle Benchmark-Tests aus"""
        if not self.connect():
            return None
        
        try:
            # Einzelne Variable Tests
            self.benchmark_single_bool_write(iterations=1000)
            time.sleep(1)  # Kurze Pause zwischen Tests
            
            self.benchmark_single_int16_write(iterations=1000)
            time.sleep(1)
            
            self.benchmark_single_int32_write(iterations=1000)
            time.sleep(1)
            
            # Bulk Data Tests
            self.benchmark_bulk_data_write(iterations=100)
            time.sleep(1)
            
            self.benchmark_bulk_data_read(iterations=100)
            time.sleep(1)
            
            # Mixed Operations
            self.benchmark_mixed_operations(iterations=500)
            
        finally:
            self.disconnect()
        
        return self.results
    
    def save_results(self, filename: str = None):
        """Speichert die Benchmark-Ergebnisse in einer JSON-Datei"""
        if filename is None:
            filename = f"opcua_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Ergebnisse gespeichert in: {filename}")
        return filename
    
    def print_summary(self):
        """Gibt eine Zusammenfassung der Ergebnisse aus"""
        print("\n" + "="*70)
        print("OPC UA PERFORMANCE BENCHMARK - ZUSAMMENFASSUNG")
        print("="*70)
        print(f"Server: {self.results['server']}")
        print(f"Zeitstempel: {self.results['timestamp']}")
        print("-"*70)
        
        for test_name, test_data in self.results['tests'].items():
            if 'error' not in test_data:
                print(f"\n{test_data['test']}:")
                print(f"  Iterationen: {test_data['successful']}/{test_data['iterations']}")
                print(f"  Durchschnitt: {test_data['mean_ms']} ms")
                print(f"  Median: {test_data['median_ms']} ms")
                print(f"  Min/Max: {test_data['min_ms']}/{test_data['max_ms']} ms")
                print(f"  Std.Abw.: {test_data['stdev_ms']} ms")
                print(f"  Durchsatz: {test_data['throughput_ops_per_sec']} ops/s")
        
        print("\n" + "="*70)


def main():
    """Hauptfunktion"""
    # Server-URL anpassen falls nötig
    benchmark = OPCUABenchmark(server_url="opc.tcp://192.168.10.61:4840")
    
    # Alle Tests ausführen
    results = benchmark.run_all_benchmarks()
    
    if results:
        # Zusammenfassung ausgeben
        benchmark.print_summary()
        
        # Ergebnisse speichern
        benchmark.save_results()


if __name__ == "__main__":
    main()
    