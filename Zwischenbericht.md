# Zwischenbericht

## Team

Allmer
Bierbaum
Herbst

## Aufgabenstellung

Ziel ist die Entwicklung eines Performance-Tests für drei Kommunikationsprotokolle im Zusammenspiel mit einer Siemens-S7-SPS:

- OPC UA
- Siemens Web API
- Proprietäres S7-Protokoll

Fokus liegt auf hochfrequentes Schreiben einzelner Variablen (Bool, Int16, Int32) und das übertragen eines Datenblocks mit ca. 1 kB.
Zudem sol ein Pflichtenheft erstellt werden.

## Entwicklungsumgebung

Die Implementierung erfolgt in Python unter Verwendung der folgenden Bibliotheken:

- `cryptography >= 46.0.3`
- `matplotlib >= 3.10.7`
- `opcua >= 0.98.13`
- `python-dotenv >= 1.2.1`
- `python-snap7 >= 2.0.2`
- `requests >= 2.32.5`
- `urllib3 >= 2.5.0`

## Softwarearchitektur
Es wurde für jedes Kommunikationsprotokoll ein Adapter realisiert. Alle Protokoll-Adapter implementieren eine gemeinsame abstrakte Basisklasse.

```py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

class ProtocolAdapter(ABC):
    """Abstract base class for SPS protocol adapters (e.g., WebAPI, Modbus, OPC UA)."""

    @abstractmethod
    def connect(self) -> None:
        """Establish connection or login if required."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection or logout if required."""
        pass

    @abstractmethod
    def write(self, var: str, value: Any) -> Tuple[Dict, float]:
        """Write a single value, return response and latency in ms."""
        pass

    @abstractmethod
    def read(self, var: str) -> Tuple[Dict, float]:
        """Read a single value, return response and latency in ms."""
        pass

    @abstractmethod
    def write_bulk_data(self, array_data: List[Any]) -> Tuple[Dict, float]:
        """Write an entire array of bulk data."""
        pass
```

## Datenübertragungssicherheit

Da alle Protokolle auf dem TCP-Transportprotokoll basieren, gehen wie bei einer Success Response davon aus, dass die Daten vollständig und korrekt übertragen wurden. Wir überprüfen aber nicht ob die Werte explizit in den Spicher geschrieben worden sind.