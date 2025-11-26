# normalizer-service

**Description:** ingests messy schema / files / blobs and parse them, map them to our schemas and persists the learned schemas
**URL:** https://github.com/Ai-Whisperers/normalizer-service
**Visibility:** PRIVATE

---

# 🧭 Project: **Customer-Feedback-App**

## ⚙️ Deploy & Runtime

**Stack:** Docker + Kubernetes + Apache Kafka
**Environment:** On-premise data center (no external vendor dependency).

---

## 🎨 Frontend Service (UX Layer)

**Web Service:**
Users upload feedback files (up to ≈ 2.5 M rows).
Uploads are sent to backend services via REST/gRPC.

---

## 🧠 Backend Services (Streaming Pipeline)

### **Orchestrator**

* Handles async data flow and coordination.
* Batching of streams via **Kafka topics** (decoupled I/O).
* Real-time gRPC over **Arrow Flight** for structured data exchange.

### **Parsers**

Each parser subscribes to Kafka topics by file type:

* Excel Parser Service
* JSON Parser Service
* Parquet Parser Service
* CSV Parser Service

### **Normalizers**

* Unified schema lakes (headers / NPS / comments schemas).
* Schema storage with hashing + checksums.
* Caching and streaming to Google Drive or local persistence.

### **Processor**

* Runs analytical models and insight generation.
* Falls back to GPT for semantic analysis if needed.

### **Aggregator**

* Merges processed results before frontend delivery.
* Output formats: Excel (default), optional Parquet/JSON.
* **Streaming is fast and continuous, but data is collected in micro-batches for proper structuring and aggregation.**

---

# Minimal example of Docker Compose and a single parser
"minimal Docker Compose with Kafka + Zookeeper (or KRaft) + one parser service to bootstrap your on-premise cluster setup"
Here’s a **minimal but production-ready Docker Compose** to bootstrap your on-premise Kafka + one parser microservice environment (no vendor dependencies, KRaft mode → no Zookeeper).

```yaml
# docker-compose.yml
version: "3.9"

services:
  kafka:
    image: apache/kafka:latest
    container_name: kafka
    ports:
      - "9092:9092"
      - "9093:9093"
    environment:
      # KRaft mode (no Zookeeper)
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_NODE_ID: 1
      KAFKA_CONTROLLER_QUORUM_VOTERS: "1@localhost:9093"
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_LOG_DIRS: /tmp/kraft-combined-logs
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
    volumes:
      - kafka-data:/tmp/kraft-combined-logs
    restart: always

  parser-excel:
    build: ./parser-excel
    container_name: parser-excel
    depends_on:
      - kafka
    environment:
      KAFKA_BROKER: kafka:9092
      INPUT_TOPIC: uploads.excel
      OUTPUT_TOPIC: parsed.excel
    command: ["python", "main.py"]
    volumes:
      - ./parser-excel:/app
    restart: on-failure

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: kafka-ui
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
    depends_on:
      - kafka
    restart: unless-stopped

volumes:
  kafka-data:
```

---

### 📁 Example Folder Layout

```
customer-feedback-app/
├─ docker-compose.yml
├─ parser-excel/
│  ├─ Dockerfile
│  ├─ main.py
│  └─ requirements.txt
```

### 🧩 `parser-excel/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

### 🧠 `parser-excel/requirements.txt`

```
pandas
openpyxl
confluent-kafka
pyarrow
```

### ⚡ `parser-excel/main.py` (minimal example)

```python
from confluent_kafka import Consumer, Producer
import pandas as pd, io, json, pyarrow as pa

broker = "kafka:9092"
input_topic = "uploads.excel"
output_topic = "parsed.excel"

consumer = Consumer({'bootstrap.servers': broker, 'group.id': 'excel-parser', 'auto.offset.reset': 'earliest'})
producer = Producer({'bootstrap.servers': broker})
consumer.subscribe([input_topic])

print("📥 Excel Parser Service running...")

while True:
    msg = consumer.poll(1.0)
    if msg is None or msg.error():
        continue
    try:
        buf = io.BytesIO(msg.value())
        df = pd.read_excel(buf)
        arrow_buf = pa.BufferOutputStream()
        with pa.ipc.new_file(arrow_buf, df.columns.to_list()) as writer:
            writer.write_table(pa.Table.from_pandas(df))
        producer.produce(output_topic, value=arrow_buf.getvalue().to_pybytes())
        producer.flush()
        print(f"✅ Parsed batch → {len(df)} rows")
    except Exception as e:
        print(f"❌ Error parsing Excel: {e}")
```

---

### 🚀 Run

```bash
docker compose up -d
```

Then open **[http://localhost:8080](http://localhost:8080)** → Kafka UI → verify topics.

# Minimal example with orchestrator, normalizer and aggregator
Perfect — here’s the **extended, modular stack** adding the **Normalizer**, **Aggregator**, and **Orchestrator** services, all Kafka-connected and ready for K8s or on-prem Docker deployment.

---

```yaml
# docker-compose.yml
version: "3.9"

services:
  kafka:
    image: apache/kafka:latest
    container_name: kafka
    ports:
      - "9092:9092"
      - "9093:9093"
    environment:
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_NODE_ID: 1
      KAFKA_CONTROLLER_QUORUM_VOTERS: "1@localhost:9093"
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_LOG_DIRS: /tmp/kraft-combined-logs
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
    volumes:
      - kafka-data:/tmp/kraft-combined-logs
    restart: always

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: kafka-ui
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
    depends_on:
      - kafka
    restart: unless-stopped

  parser-excel:
    build: ./parser-excel
    container_name: parser-excel
    environment:
      KAFKA_BROKER: kafka:9092
      INPUT_TOPIC: uploads.excel
      OUTPUT_TOPIC: parsed.excel
    depends_on:
      - kafka
    restart: on-failure

  normalizer:
    build: ./normalizer
    container_name: normalizer
    environment:
      KAFKA_BROKER: kafka:9092
      INPUT_TOPIC: parsed.excel
      OUTPUT_TOPIC: normalized.data
    depends_on:
      - parser-excel
    restart: on-failure

  aggregator:
    build: ./aggregator
    container_name: aggregator
    environment:
      KAFKA_BROKER: kafka:9092
      INPUT_TOPIC: normalized.data
      OUTPUT_TOPIC: aggregated.output
    depends_on:
      - normalizer
    restart: on-failure

  orchestrator:
    build: ./orchestrator
    container_name: orchestrator
    environment:
      KAFKA_BROKER: kafka:9092
      OUTPUT_TOPIC: uploads.excel
      AGGREGATED_TOPIC: aggregated.output
    depends_on:
      - aggregator
    ports:
      - "5000:5000"
    restart: on-failure

volumes:
  kafka-data:
```

---

### 📁 Folder layout

```
customer-feedback-app/
├─ docker-compose.yml
├─ parser-excel/
│  ├─ Dockerfile
│  ├─ main.py
│  └─ requirements.txt
├─ normalizer/
│  ├─ Dockerfile
│  ├─ main.py
│  └─ requirements.txt
├─ aggregator/
│  ├─ Dockerfile
│  ├─ main.py
│  └─ requirements.txt
└─ orchestrator/
   ├─ Dockerfile
   ├─ main.py
   └─ requirements.txt
```

---

### 🧩 Example: **normalizer/main.py**

```python
from confluent_kafka import Consumer, Producer
import pandas as pd, pyarrow as pa, json, io

broker = "kafka:9092"
input_topic = "parsed.excel"
output_topic = "normalized.data"

consumer = Consumer({'bootstrap.servers': broker, 'group.id': 'normalizer', 'auto.offset.reset': 'earliest'})
producer = Producer({'bootstrap.servers': broker})
consumer.subscribe([input_topic])

print("🧩 Normalizer Service running...")

while True:
    msg = consumer.poll(1.0)
    if msg is None or msg.error(): 
        continue
    try:
        df = pa.ipc.open_file(io.BytesIO(msg.value())).read_all().to_pandas()
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        df = df.fillna("")
        payload = df.to_json(orient="records")
        producer.produce(output_topic, value=payload.encode())
        producer.flush()
        print(f"✅ Normalized {len(df)} records")
    except Exception as e:
        print(f"❌ Normalizer error: {e}")
```

---

### 🧮 **aggregator/main.py**

```python
from confluent_kafka import Consumer, Producer
import pandas as pd, json, io, time

broker = "kafka:9092"
input_topic = "normalized.data"
output_topic = "aggregated.output"

consumer = Consumer({'bootstrap.servers': broker, 'group.id': 'aggregator', 'auto.offset.reset': 'earliest'})
producer = Producer({'bootstrap.servers': broker})
consumer.subscribe([input_topic])

print("📊 Aggregator Service running...")

buffer = []
while True:
    msg = consumer.poll(1.0)
    if msg is None or msg.error():
        continue
    try:
        data = json.loads(msg.value())
        buffer.extend(data)
        if len(buffer) >= 5000:  # micro-batch
            df = pd.DataFrame(buffer)
            summary = {
                "rows": len(df),
                "columns": list(df.columns),
                "timestamp": time.time()
            }
            producer.produce(output_topic, value=json.dumps(summary).encode())
            producer.flush()
            buffer.clear()
            print(f"✅ Aggregated {summary['rows']} rows")
    except Exception as e:
        print(f"❌ Aggregator error: {e}")
```

---

### ⚙️ **orchestrator/main.py**

```python
from flask import Flask, request, jsonify
from confluent_kafka import Producer
import os

app = Flask(__name__)
producer = Producer({'bootstrap.servers': os.getenv("KAFKA_BROKER", "kafka:9092")})
topic = os.getenv("OUTPUT_TOPIC", "uploads.excel")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files['file']
    data = file.read()
    producer.produce(topic, value=data)
    producer.flush()
    return jsonify({"status": "queued", "bytes": len(data)})

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

---

### 🧠 Data Flow Summary

```
[Frontend] → /upload → Orchestrator → Kafka (uploads.excel)
     ↓
Parser → Kafka (parsed.excel)
     ↓
Normalizer → Kafka (normalized.data)
     ↓
Aggregator → Kafka (aggregated.output)
     ↓
Frontend/UI fetches structured summaries or analytics
```

---

### 🚀 Run locally

```bash
docker compose up -d --build
```

→ Upload file:

```bash
curl -F "file=@test.xlsx" http://localhost:5000/upload
```

→ Inspect flow in **[http://localhost:8080](http://localhost:8080)** (Kafka UI).


# LLM addition and NPS scoring
Perfect — here’s the **next stage** adding your **Processor Service** for AI/NLP sentiment & insights analysis (with GPT fallback, minimal vendor coupling).

---

```yaml
# docker-compose.yml (append after aggregator)
version: "3.9"

services:
  kafka:
    image: apache/kafka:latest
    container_name: kafka
    ports:
      - "9092:9092"
      - "9093:9093"
    environment:
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_NODE_ID: 1
      KAFKA_CONTROLLER_QUORUM_VOTERS: "1@localhost:9093"
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_LOG_DIRS: /tmp/kraft-combined-logs
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
    volumes:
      - kafka-data:/tmp/kraft-combined-logs
    restart: always

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: kafka-ui
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
    depends_on:
      - kafka
    restart: unless-stopped

  parser-excel:
    build: ./parser-excel
    environment:
      KAFKA_BROKER: kafka:9092
      INPUT_TOPIC: uploads.excel
      OUTPUT_TOPIC: parsed.excel
    depends_on: [kafka]
    restart: on-failure

  normalizer:
    build: ./normalizer
    environment:
      KAFKA_BROKER: kafka:9092
      INPUT_TOPIC: parsed.excel
      OUTPUT_TOPIC: normalized.data
    depends_on: [parser-excel]
    restart: on-failure

  processor:
    build: ./processor
    container_name: processor
    environment:
      KAFKA_BROKER: kafka:9092
      INPUT_TOPIC: normalized.data
      OUTPUT_TOPIC: processed.data
      HF_MODEL: cardiffnlp/twitter-roberta-base-sentiment-latest
    depends_on: [normalizer]
    restart: on-failure

  aggregator:
    build: ./aggregator
    environment:
      KAFKA_BROKER: kafka:9092
      INPUT_TOPIC: processed.data
      OUTPUT_TOPIC: aggregated.output
    depends_on: [processor]
    restart: on-failure

  orchestrator:
    build: ./orchestrator
    ports: ["5000:5000"]
    environment:
      KAFKA_BROKER: kafka:9092
      OUTPUT_TOPIC: uploads.excel
      AGGREGATED_TOPIC: aggregated.output
    depends_on: [aggregator]
    restart: on-failure

volumes:
  kafka-data:
```

---

### 📁 Processor folder

```
processor/
├─ Dockerfile
├─ requirements.txt
└─ main.py
```

---

### 🧩 `processor/requirements.txt`

```
transformers
torch
confluent-kafka
pandas
pyarrow
```

---

### ⚙️ `processor/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

---

### 🧠 `processor/main.py`

```python
from confluent_kafka import Consumer, Producer
from transformers import pipeline
import pandas as pd, json, io, pyarrow as pa

broker = "kafka:9092"
input_topic = "normalized.data"
output_topic = "processed.data"

consumer = Consumer({'bootstrap.servers': broker, 'group.id': 'processor', 'auto.offset.reset': 'earliest'})
producer = Producer({'bootstrap.servers': broker})
consumer.subscribe([input_topic])

print("🤖 Processor Service running...")

# sentiment/intent model (lightweight fallback if no GPT)
nlp = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")

while True:
    msg = consumer.poll(1.0)
    if msg is None or msg.error(): 
        continue
    try:
        records = json.loads(msg.value())
        df = pd.DataFrame(records)
        if "comment" in df.columns:
            df["analysis"] = df["comment"].apply(lambda c: nlp(c[:512])[0])
        else:
            df["analysis"] = "N/A"

        result = df.to_json(orient="records")
        producer.produce(output_topic, value=result.encode())
        producer.flush()
        print(f"✅ Processed {len(df)} records")
    except Exception as e:
        print(f"❌ Processor error: {e}")
```

---

### 🔄 Updated flow

```
Orchestrator (/upload)
 → Kafka [uploads.excel]
 → Parser (Excel → Arrow)
 → Kafka [parsed.excel]
 → Normalizer (schema unification)
 → Kafka [normalized.data]
 → Processor (sentiment/NLP/GPT fallback)
 → Kafka [processed.data]
 → Aggregator (batch summaries)
 → Kafka [aggregated.output]
 → Frontend fetches insights
```

---

### 🧪 Run

```bash
docker compose up -d --build
curl -F "file=@sample.xlsx" http://localhost:5000/upload
```

→ Track pipeline in **Kafka UI** (`http://localhost:8080`).

---

# Optional GPT fallback logic

Here’s the **final extension**: your **Processor Service with GPT fallback**, designed to stay *fully on-prem and self-governed* — it only calls an external LLM endpoint if explicitly enabled.

---

### 🧩 Updated `processor/main.py`

```python
from confluent_kafka import Consumer, Producer
from transformers import pipeline
import pandas as pd, json, io, os, requests

broker = os.getenv("KAFKA_BROKER", "kafka:9092")
input_topic = os.getenv("INPUT_TOPIC", "normalized.data")
output_topic = os.getenv("OUTPUT_TOPIC", "processed.data")

gpt_endpoint = os.getenv("GPT_ENDPOINT")           # optional, e.g. http://localhost:8089/v1/chat/completions
gpt_key = os.getenv("GPT_API_KEY")                 # optional
gpt_model = os.getenv("GPT_MODEL", "gpt-4o-mini")  # safe default

consumer = Consumer({'bootstrap.servers': broker, 'group.id': 'processor', 'auto.offset.reset': 'earliest'})
producer = Producer({'bootstrap.servers': broker})
consumer.subscribe([input_topic])

print("🤖 Processor Service running... (local NLP + optional GPT fallback)")

nlp = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")

def gpt_fallback(text: str) -> str:
    """Call external GPT only if endpoint & key are set"""
    if not gpt_endpoint or not gpt_key:
        return "GPT_DISABLED"
    try:
        payload = {
            "model": gpt_model,
            "messages": [{"role": "user", "content": f"Analyze sentiment and summarize this feedback:\n{text}"}],
            "max_tokens": 100,
        }
        headers = {"Authorization": f"Bearer {gpt_key}", "Content-Type": "application/json"}
        resp = requests.post(gpt_endpoint, headers=headers, json=payload, timeout=10)
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"⚠️ GPT fallback error: {e}")
        return "GPT_ERROR"

while True:
    msg = consumer.poll(1.0)
    if msg is None or msg.error(): 
        continue
    try:
        records = json.loads(msg.value())
        df = pd.DataFrame(records)

        if "comment" in df.columns:
            df["analysis"] = [
                nlp(c[:512])[0] if c and len(c) > 0 else {"label": "neutral", "score": 0.0}
                for c in df["comment"]
            ]
            # optional GPT refinement
            if gpt_endpoint and gpt_key:
                df["gpt_summary"] = df["comment"].apply(gpt_fallback)
            else:
                df["gpt_summary"] = "GPT_DISABLED"
        else:
            df["analysis"] = "N/A"
            df["gpt_summary"] = "N/A"

        result = df.to_json(orient="records")
        producer.produce(output_topic, value=result.encode())
        producer.flush()
        print(f"✅ Processed {len(df)} records")
    except Exception as e:
        print(f"❌ Processor error: {e}")
```

---

### ⚙️ Optional ENV configuration (in `docker-compose.yml`)

```yaml
  processor:
    build: ./processor
    environment:
      KAFKA_BROKER: kafka:9092
      INPUT_TOPIC: normalized.data
      OUTPUT_TOPIC: processed.data
      HF_MODEL: cardiffnlp/twitter-roberta-base-sentiment-latest
      GPT_ENDPOINT: http://localhost:8089/v1/chat/completions   # optional
      GPT_API_KEY: sk-local-xxxxxx                              # optional
      GPT_MODEL: gpt-4o-mini                                    # optional
```

---

### 🧱 Behavior summary

| Mode          | Trigger            | Behavior                                              |
| ------------- | ------------------ | ----------------------------------------------------- |
| **Offline**   | No `GPT_ENDPOINT`  | Uses only local `transformers` sentiment model.       |
| **Hybrid**    | `GPT_ENDPOINT` set | Adds GPT summaries after local analysis.              |
| **Fail-safe** | Network/API error  | Falls back silently, keeps processing pipeline alive. |

---

### 🔄 Updated data flow

```
Normalizer → Kafka [normalized.data]
     ↓
Processor → local transformer → optional GPT summary
     ↓
Kafka [processed.data]
     ↓
Aggregator → structured summaries
     ↓
Frontend (UX insight dashboard)
```

---

### 🧠 Design advantages

* ✅ 100 % functional offline (transformers only).
* ✅ Optional AI enhancement if GPT server is available (local or cloud).
* 🧩 Plug-and-play: any HTTP-compatible model (OpenAI, vLLM, Ollama, local llama.cpp) works.
* 🛡️ Isolation: no vendor lock-in; full on-prem control of data flow.
