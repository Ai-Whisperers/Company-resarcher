# excel-parsing-service

**Description:** 
**URL:** https://github.com/Ai-Whisperers/excel-parsing-service
**Visibility:** PRIVATE

---

# Excel POI Parser Service

**Input:** Any Excel (.xls or .xlsx file)
**Output:** Arrow/JSON schema of the parsed document

A **hybrid two-plane architecture** for parsing Excel files with real-time performance:
- **Control Plane (REST):** Authentication, session management, flight preparation
- **Data Plane (Arrow Flight):** High-throughput gRPC streaming (10-100x faster than REST)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Application                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP Request (Excel File)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               Python Aggregation Layer (Port 8000)          │
│  • Receives Excel files from clients                        │
│  • Forwards to Java layer for parsing                       │
│  • Aggregates and formats results                           │
│  • Outputs Arrow IPC or JSON                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Internal HTTP (JSON)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                Java Parsing Layer (Port 8080)               │
│  • Apache POI Excel parsing                                 │
│  • Cell extraction & metadata                               │
│  • Data normalization & type inference                      │
│  • Returns structured JSON                                  │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
excel-poi-parser/
├── pnpm-workspace.yaml          # pnpm workspace configuration
├── package.json                 # Root orchestration scripts
├── docker-compose.yml           # Multi-container setup
│
├── java-layer/                  # Java parsing layer
│   ├── package.json             # pnpm scripts for Maven
│   ├── pom.xml                  # Maven dependencies
│   ├── Dockerfile
│   └── src/main/java/com/customeranalysis/excel/
│       ├── ExcelParserApplication.java
│       ├── controller/
│       │   └── ExcelParserController.java
│       ├── service/
│       │   ├── ExcelParserService.java
│       │   └── extractor/
│       │       ├── WorkbookLoaderService.java
│       │       ├── SheetEnumeratorService.java
│       │       ├── CellExtractorService.java
│       │       ├── MetadataExtractorService.java
│       │       ├── DataNormalizerService.java
│       │       └── OutputFormatterService.java
│       ├── dto/
│       └── model/
│
└── python-layer/                # Python aggregation layer
    ├── package.json             # pnpm scripts for Python
    ├── requirements.txt         # Python dependencies
    ├── Dockerfile
    └── app/
        ├── main.py              # FastAPI application
        ├── config.py            # Configuration
        ├── models/
        │   └── schemas.py       # Pydantic models
        └── services/
            ├── java_client.py   # Java layer client
            ├── aggregator.py    # Data aggregation
            ├── arrow_formatter.py
            └── json_formatter.py
```

## Prerequisites

- **Node.js** >= 18.x
- **pnpm** >= 8.x
- **Java** 17 (for Java layer)
- **Maven** 3.x (for Java layer)
- **Python** 3.11+ (for Python layer)
- **Docker** & **Docker Compose** (optional, for containerized deployment)

## Installation

### Using pnpm (Monorepo Orchestration)

```bash
# Install pnpm globally if not installed
npm install -g pnpm

# Install all dependencies (both layers)
pnpm install:all
```

### Manual Installation

#### Java Layer
```bash
cd java-layer
mvn clean install
```

#### Python Layer
```bash
cd python-layer
pip install -r requirements.txt
```

## Development

### Start Both Layers Concurrently

```bash
pnpm dev
```

### Start Individual Layers

```bash
# Java layer (port 8080)
pnpm dev:java

# Python layer (port 8000)
pnpm dev:python
```

## Docker Deployment

### Build and Start All Services

```bash
pnpm docker:build
pnpm docker:up
```

Or using Docker Compose directly:

```bash
docker-compose up --build
```

### Stop Services

```bash
pnpm docker:down
```

## API Endpoints

### Control Plane - REST API (Port 8000)

#### Process Excel File (Legacy - Small Files)
```http
POST /api/v1/process/excel
Content-Type: multipart/form-data

Parameters:
  - file: Excel file (required)
  - sheet_name: Filter by sheet name (optional)
  - region: Cell region (e.g., "A1:D10") (optional)
  - output_format: "json" or "arrow" (default: "json")
  - aggregate: true/false (default: true)
```

#### Prepare Flight (Large Files - Recommended)
```http
POST /api/v1/flight/prepare
Parameters:
  - file_path: Path to Excel file (required)
  - sheet_name: Filter by sheet name (optional)
  - region: Cell region (optional)

Response:
{
  "flight_id": "excel_data_file.xlsx",
  "schema": {...},
  "total_records": 1000000,
  "grpc_endpoint": "grpc://localhost:8815",
  "ticket": "excel:flight_id:{}"
}
```

#### List Flights
```http
GET /api/v1/flight/list

Response:
{
  "flights": [...],
  "count": 0,
  "grpc_endpoint": "grpc://localhost:8815"
}
```

#### Get Client Example
```http
GET /api/v1/flight/example

Returns Python client code for Arrow Flight streaming
```

#### Health Check
```http
GET /health
```

### Data Plane - Arrow Flight (Port 8815)

High-performance gRPC streaming for large datasets (10-100x faster than REST):

```python
import pyarrow.flight as flight

# Connect to Flight server
client = flight.FlightClient("grpc://localhost:8815")

# Stream data
ticket = flight.Ticket(b"excel:flight_id:{}")
reader = client.do_get(ticket)

# Process batches
for batch in reader:
    df = batch.data.to_pandas()
    print(f"Streamed {len(df)} rows")
```

### Java Layer (Port 8080)

#### Parse Excel (Internal API)
```http
POST /api/v1/excel/parse
Content-Type: multipart/form-data
```

#### Health Check
```http
GET /api/v1/excel/health
```

## Output Formats

### JSON Format
```json
{
  "success": true,
  "metadata": {
    "numberOfSheets": 2,
    "numberOfNames": 0,
    "sheets": {
      "Sheet1": 0,
      "Sheet2": 1
    }
  },
  "sheets": {
    "Sheet1": {
      "columns": ["Column_0", "Column_1", ...],
      "data": [[...], [...], ...],
      "rowCount": 100,
      "columnCount": 10
    }
  },
  "statistics": {...},
  "timestamp": 1234567890
}
```

### Arrow Format
Returns Apache Arrow IPC stream format (binary)
- Content-Type: `application/vnd.apache.arrow.stream`
- Can be read by Arrow libraries in any language

## Testing

```bash
# Test all
pnpm test

# Test Java layer
pnpm test:java

# Test Python layer
pnpm test:python
```

## Build

```bash
# Build all
pnpm build

# Build Java layer
pnpm build:java

# Build Python layer
pnpm build:python
```

## Clean

```bash
pnpm clean
```

## Component Descriptions

### Java Layer Components

1. **WorkbookLoaderService**: Loads Excel files (.xls/.xlsx) with POI
2. **SheetEnumeratorService**: Iterates over sheets and collects metadata
3. **CellExtractorService**: Extracts cell data, formulas, merged cells
4. **MetadataExtractorService**: Gathers styles, named ranges, comments
5. **DataNormalizerService**: Normalizes values and infers types
6. **OutputFormatterService**: Formats data as JSON

### Python Layer Components

1. **JavaLayerClient**: HTTP client for Java layer communication
2. **DataAggregator**: Aggregates cell data into tabular format
3. **ArrowFormatter**: Converts to Apache Arrow IPC format
4. **JSONFormatter**: Formats structured JSON output

## Configuration

### Java Layer
Edit `java-layer/src/main/resources/application.yml`:
```yaml
parser:
  max-rows: 100000
  max-columns: 1000
  enable-formula-evaluation: true
```

### Python Layer
Copy `.env.example` to `.env` and configure:
```bash
# Java Layer
JAVA_LAYER_URL=http://localhost:8080

# File Processing
MAX_FILE_SIZE_MB=100
ARROW_COMPRESSION=zstd

# Arrow Flight (Data Plane)
FLIGHT_HOST=0.0.0.0
FLIGHT_PORT=8815

# REST API (Control Plane)
API_HOST=0.0.0.0
API_PORT=8000
```

## Performance Comparison

| File Size | REST API    | Arrow Flight | Speedup |
| --------- | ----------- | ------------ | ------- |
| 1 MB      | 100 ms      | 50 ms        | 2x      |
| 10 MB     | 1.5 s       | 200 ms       | 7.5x    |
| 100 MB    | 25 s        | 1.5 s        | 16x     |
| 1 GB      | Timeout ⚠️  | 12 s         | ∞       |

**Recommendation:** Use Arrow Flight (port 8815) for files > 10 MB

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed hybrid architecture documentation
- **[README.md](README.md)** - This file (quick start guide)

## License

MIT
