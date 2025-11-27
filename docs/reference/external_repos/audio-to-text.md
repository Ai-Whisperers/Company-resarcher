# audio-to-text

**Description:** transcriptor bundle ai token-free (only whisper lib)
**URL:** https://github.com/Ai-Whisperers/audio-to-text
**Visibility:** PRIVATE

---

# Transcriptor MVP

**Intelligent Audio Transcription System with OpenAI Whisper**

A complete modular audio transcription system featuring dynamic model selection, semantic post-processing, intelligent summarization, and batch processing capabilities.

---

## ⭐ Key Features

### Core Capabilities
- **Multi-format Support**: M4A, MP3, WAV, FLAC, OGG, AAC, WMA, OPUS, WebM
- **Two-Phase Transcription**: Quick preview (TINY model) + High-quality final (auto-selected model)
- **Dynamic Model Selection**: Automatically chooses optimal Whisper model based on audio characteristics
- **99 Languages**: Full multilingual support via Whisper

### Advanced Features
- **AI-Powered Handbook Generation**: SmolLM2-based handbook creator (User Guides, Technical Docs, FAQ)
- **Semantic Post-Processing**: LLM-ready Markdown and token-efficient formats
- **Intelligent Summarization**: Extractive summaries with key points extraction
- **Batch Processing**: Process entire folders with resume capability and progress tracking
- **Multiple Output Formats**: TXT, SRT, VTT, JSON, Markdown, Summaries, Handbooks
- **GPU Acceleration**: Automatic CUDA detection and utilization (5-10x faster)

### Quality & Performance
- **Audio Preprocessing**: Quality analysis, normalization, noise reduction
- **Result Caching**: SHA256-based caching with TTL (100-1000x speedup for repeated files)
- **Parallel Processing**: Multi-worker batch processing (2-4x speedup)
- **Memory Management**: Automatic model selection based on available RAM with optimized cleanup
- **Progress Tracking**: Real-time tqdm progress bars for batch operations
- **Performance Benchmarking**: Built-in benchmark suite to measure optimizations

---

## 🚀 Quick Start

**See [Quick Start Guide](../../../docs/QUICK_START.md) for detailed instructions**

### 1. Install Prerequisites

```bash
# Install FFmpeg
# Windows: Download from ffmpeg.org
# macOS: brew install ffmpeg
# Linux: sudo apt-get install ffmpeg

# Install Python packages
pip install -r requirements.txt
```

### 2. Process Your First Audio

```bash
# Add audio file to ingestion folder
cp your-audio.m4a ingestion/

# Transcribe
python app.py process ingestion/your-audio.m4a

# View result
cat output/your-audio_final.txt
```

### 3. Batch Process Multiple Files

```bash
# Add multiple files
cp *.m4a ingestion/

# Process all (sequential)
python batch_process.py

# Process all (parallel - 4 workers for 4x speedup)
# Edit batch_process.py: BatchProcessor(parallel=True, max_workers=4)

# Generate summaries
python generate_summaries.py
```

---

## 📚 Documentation

**Complete documentation in the `docs/` folder:**

| Document | Purpose |
|----------|---------|
| **[Quick Start](../../../docs/QUICK_START.md)** | Get started in 5 minutes |
| **[User Guide](../../../docs/USER_GUIDE.md)** | Complete usage documentation |
| **[Configuration](../../../docs/CONFIGURATION.md)** | All settings explained |
| **[Performance](../../../docs/PERFORMANCE.md)** | Optimization & tuning guide |
| **[Testing](../../../docs/TESTING.md)** | Testing guide & coverage |
| **[Module Reference](../../../docs/MODULE_REFERENCE.md)** | Technical documentation |
| **[Troubleshooting](../../../docs/TROUBLESHOOTING.md)** | Common issues & solutions |

**→ Start here: [docs/README.md](../../../docs/README.md)**

---

## 🎯 Common Use Cases

### Single File Transcription
```bash
python app.py process ingestion/meeting.m4a
```

### Batch Processing
```bash
python batch_process.py
```

### Generate Summaries
```bash
python generate_summaries.py
```

### Monitor Progress
```bash
python check_progress.py
```

### Test Semantic Processing
```bash
python test_semantic.py
```

---

## 🏗️ System Architecture

The system consists of **10 specialized modules** working together:

```
Input (M4A, MP3, etc.)
    ↓
[1] Observer → Canonical WAV (16kHz, mono, PCM16)
    ↓
[2] Format Converter → Multi-format support
    ↓
[3] Preprocessor → Quality analysis
    ↓
[4] Model Selector → Choose optimal Whisper model
    ↓
[5] Transcriptor → Preview + Final transcription (with caching)
    ↓
[6] Output Handler → TXT, SRT, JSON exports
    ↓
[7] Semantic Processor → LLM-ready formatting
    ↓
[8] Summarizer → Intelligent summaries
    ↓
[9] Document Generator → AI-powered handbooks
    ↓
Results + Handbooks
```

**Module Details:**

1. **Observer** (`observer.py`) - Input capture and canonicalization
2. **Format Converter** (`format_converter.py`) - Multi-format audio conversion
3. **Preprocessor** (`preprocessor.py`) - Audio quality analysis
4. **Model Selector** (`model_selector.py`) - Dynamic Whisper model selection
5. **Transcriptor** (`transcriptor.py`) - Two-phase transcription execution with caching
6. **Output Handler** (`output_handler.py`) - Multi-format output generation
7. **Semantic Processor** (`semantic_processor.py`) - LLM-ready post-processing
8. **Summarizer** (`summarizer.py`) - Extractive summarization
9. **Document Generator** (`document_generator.py`) - AI-powered handbook generation (SmolLM2)
10. **Cache Manager** (`cache_manager.py`) - SHA256-based result caching with TTL

**Orchestration:**
- **Pipeline** (`pipeline.py`) - Coordinates all modules
- **App Entry Point** (`app.py`) - CLI interface and main controller
- **Batch Processor** (`batch_process.py`) - Batch operations with resume and parallel support

## Installation

### Prerequisites

- Python 3.8 or higher
- FFmpeg installed and in PATH

### Install FFmpeg

**Windows:**
```bash
# Download from https://ffmpeg.org/download.html
# Or use Chocolatey:
choco install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

## 📋 Available Commands

### Main Commands

```bash
# Single file transcription
python app.py process ingestion/audio.m4a

# Quick preview only (fast)
python app.py preview ingestion/audio.m4a

# Batch process all files in ingestion folder
python batch_process.py

# Generate summaries from transcriptions
python generate_summaries.py

# Check batch processing progress
python check_progress.py

# Test semantic processing on existing file
python test_semantic.py

# Run performance benchmarks
python benchmark.py test_audio.wav

# Run test suite
pytest
```

### Configuration

All settings are controlled via `config.json`. See [Configuration Reference](../../../docs/CONFIGURATION.md) for details.

**Common adjustments:**

Force specific model:
```json
{
  "model_selection": {
    "force_model": "medium"
  }
}
```

Change language:
```json
{
  "transcription": {
    "language": "es"
  }
}
```

Adjust output formats:
```json
{
  "output": {
    "formats": ["txt", "json"]
  }
}
```

Enable result caching:
```json
{
  "enable_cache": true,
  "cache_dir": ".cache",
  "cache_ttl": 86400
}
```

## Configuration

Edit `config.json` to customize behavior:

```json
{
  "preprocessing": {
    "noise_reduction": true,
    "normalization": true,
    "trim_silence": true
  },
  "model_selection": {
    "preview_model": "tiny",
    "auto_select": true,
    "device": "auto"
  },
  "transcription": {
    "language": "en",
    "timestamps": true
  },
  "output": {
    "formats": ["txt", "srt", "json"],
    "output_dir": "./output"
  }
}
```

## 🤖 Whisper Models

The system automatically selects the optimal model based on audio duration and quality.

| Model  | Parameters | RAM   | CPU Speed | GPU Speed | Best For                    |
|--------|-----------|-------|-----------|-----------|----------------------------|
| tiny   | 39M       | ~1GB  | 0.1x RT   | 0.02x RT  | Quick preview, <30s audio  |
| base   | 74M       | ~1GB  | 0.2x RT   | 0.05x RT  | Short audio, <2min         |
| small  | 244M      | ~2GB  | 0.3x RT   | 0.1x RT   | Medium audio, <10min       |
| medium | 769M      | ~5GB  | 0.5x RT   | 0.15x RT  | Long audio, >10min         |
| large  | 1550M     | ~10GB | 1.0x RT   | 0.3x RT   | High-quality, complex audio|

*RT = Realtime (0.5x RT = 10 min audio processed in 5 min)*

**Auto-Selection Algorithm:**
- **< 30s**: TINY
- **< 2 min, good quality**: BASE
- **< 10 min**: SMALL
- **< 30 min**: MEDIUM
- **≥ 30 min**: LARGE (with memory check, fallback to MEDIUM)

See [Configuration Reference](../../../docs/CONFIGURATION.md#model-selection) for manual override.

## 📄 Output Formats

Each transcription generates multiple output files:

### Core Outputs

**TXT** (`*_final.txt`)
- Plain text transcription
- Best for reading or copying
- ~5-10KB per minute of audio

**SRT** (`*_final.srt`)
- SubRip subtitle format with timestamps
- Compatible with video players
- Time-synced segments

```
1
00:00:00,000 --> 00:00:05,000
This is the transcribed text.
```

**JSON** (`*_final.json`)
- Complete structured data with all segments
- Most detailed format
- ~20-50KB per minute

```json
{
  "text": "Full transcription...",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 5.0,
      "text": "Segment text"
    }
  ],
  "model": "medium",
  "language": "en",
  "duration": 163.5
}
```

### Semantic Outputs

**Markdown** (`*_semantic.md`)
- LLM-ready format with paragraphs
- Includes metadata and statistics
- Properly formatted for AI consumption

**LLM Format** (`*_llm.txt`)
- Token-efficient text format
- Optimized for LLM context windows
- Minimal overhead

**Analysis** (`*_analysis.json`)
- Semantic statistics
- Word count, sentence count, reading time
- Content analysis metadata

### Summary Outputs

Generated by `generate_summaries.py` in `output/summaries/`:

**Summary Text** (`*_summary.txt`)
- Condensed version (typically 5-15% of original)
- Plain text format

**Summary Markdown** (`*_summary.md`)
- Formatted with sections:
  - Source information
  - Summary statistics
  - Key points (5-8 important sentences)
  - Summary text

**Summary JSON** (`*_summary.json`)
- Complete summary data
- Includes statistics and compression ratio

### Handbook Outputs (AI-Generated)

Generated automatically (if enabled) in `output/handbooks/`:

**User Guide** (`*_user-guide.md`)
- User-friendly handbook with step-by-step instructions
- Generated using SmolLM2-1.7B-Instruct
- Clear structure with tips and best practices

**Technical Documentation** (`*_technical-doc.md`)
- Technical reference format
- Specifications and detailed procedures
- Requirements and prerequisites

**FAQ Handbook** (`*_faq-handbook.md`)
- Question & answer format
- Quick reference guide
- Common questions addressed

**Configuration:**
```json
{
  "document_generation": {
    "enable": true,
    "formats": ["user_guide", "technical_doc", "faq_handbook"]
  }
}
```

**Generation Time:**
- GPU: ~30-90 seconds for all 3 formats
- CPU: ~3-9 minutes for all 3 formats

### Preview Output

**Preview Text** (`*_preview.txt`)
- Quick TINY model transcription
- Fast preview for verification
- Generated in seconds

See [User Guide - Output Files](../../../docs/USER_GUIDE.md#output-files) for details.

## 🔄 Processing Workflow

### Single File Processing

```
1. Observer
   ├─ Capture input file (M4A, MP3, etc.)
   ├─ Extract metadata (duration, codec, etc.)
   └─ Convert to canonical WAV (PCM16, mono, 16kHz)

2. Preprocessor
   ├─ Analyze audio quality
   ├─ Calculate quality score (0-100)
   └─ Apply normalization

3. Model Selector - Quick Sweep
   ├─ Fast preview with TINY model
   ├─ Show preview in 5-10 seconds
   └─ Analyze audio complexity

4. Model Selector - Choose Model
   ├─ Consider duration + quality
   ├─ Check available memory
   └─ Select optimal model (SMALL/MEDIUM/LARGE)

5. Transcriptor - Final
   ├─ Check cache for existing result
   ├─ Load selected model (if cache miss)
   ├─ High-quality transcription
   ├─ Generate segments with timestamps
   └─ Cache result for future use

6. Output Handler
   ├─ Export TXT, SRT, JSON
   ├─ Generate comparison report
   └─ Save metadata

7. Semantic Processor
   ├─ Clean text (remove fillers)
   ├─ Detect paragraphs
   ├─ Generate Markdown
   └─ Create LLM-optimized format

8. Summarizer
   ├─ Extract key sentences
   ├─ Generate summary text
   └─ Save summary files

9. Document Generator (if enabled)
   ├─ Load SmolLM2 model
   ├─ Generate User Guide
   ├─ Generate Technical Doc
   ├─ Generate FAQ Handbook
   └─ Save to output/handbooks/

10. Results Ready
   └─ All formats saved to output/
```

### Batch Processing Workflow

```
1. Scan ingestion folder for .m4a files
2. Load progress from batch_progress.json
3. For each file:
   ├─ Skip if already processed
   ├─ Run complete pipeline
   ├─ Save progress
   └─ Move to ingestion/processed/
4. All files processed
5. Run generate_summaries.py
6. Summaries saved to output/summaries/
```

See [User Guide - Basic Workflows](../../../docs/USER_GUIDE.md#basic-workflows) for details.

## 📁 Directory Structure

```
transcriptor-mvp/
├── Core Modules
│   ├── observer.py              # Input capture & canonicalization
│   ├── format_converter.py      # Multi-format audio conversion
│   ├── preprocessor.py          # Audio quality analysis
│   ├── model_selector.py        # Dynamic model selection
│   ├── transcriptor.py          # Whisper transcription with caching
│   ├── cache_manager.py         # Result caching (SHA256 + TTL)
│   ├── output_handler.py        # Multi-format export
│   ├── semantic_processor.py    # LLM-ready formatting
│   ├── summarizer.py            # Extractive summarization
│   └── document_generator.py    # AI-powered handbook generation
│
├── Orchestration
│   ├── app.py                   # Main entry point
│   ├── pipeline.py              # Workflow coordinator
│   └── batch_process.py         # Batch processing (parallel support)
│
├── Utilities
│   ├── check_progress.py        # Progress monitoring
│   ├── test_semantic.py         # Test semantic processing
│   ├── generate_summaries.py    # Batch summary generation
│   ├── benchmark.py             # Performance benchmarking
│   ├── config_utils.py          # Config helpers
│   └── logging_config.py        # Centralized logging
│
├── Configuration
│   ├── config.json              # System configuration
│   ├── requirements.txt         # Python dependencies
│   └── requirements-dev.txt     # Development dependencies
│
├── Documentation
│   ├── README.md                # This file
│   ├── architecture.md          # System architecture
│   ├── QUICK_START.md           # Quick start (legacy)
│   ├── README_SUMMARIES.md      # Summary docs (legacy)
│   ├── docs/                    # Complete documentation
│   │   ├── README.md            # Documentation index
│   │   ├── QUICK_START.md       # 5-minute guide
│   │   ├── USER_GUIDE.md        # Complete user guide
│   │   ├── CONFIGURATION.md     # Config reference
│   │   ├── PERFORMANCE.md       # Optimization guide
│   │   ├── TESTING.md           # Testing guide
│   │   ├── MODULE_REFERENCE.md  # Technical docs
│   │   └── TROUBLESHOOTING.md   # Common issues
│   └── local-reports/           # Phase completion reports
│
├── Testing
│   ├── pytest.ini               # Pytest configuration
│   ├── conftest.py              # Shared test fixtures
│   └── tests/                   # Test suite (181 tests, 94% pass)
│       ├── unit/                # Unit tests
│       │   ├── test_observer.py
│       │   ├── test_format_converter.py
│       │   ├── test_model_selector.py
│       │   ├── test_config_utils.py
│       │   └── test_logging_config.py
│       └── integration/         # Integration tests
│           └── test_app.py
│
├── Input/Output (auto-created)
│   ├── ingestion/               # Input folder
│   │   ├── *.m4a               # Audio files
│   │   └── processed/          # Completed files
│   ├── output/                  # Results folder
│   │   ├── *_preview.txt       # Quick previews
│   │   ├── *_final.txt         # Full transcriptions
│   │   ├── *_final.srt         # Subtitles
│   │   ├── *_final.json        # Complete data
│   │   ├── *_semantic.md       # LLM-ready Markdown
│   │   ├── *_llm.txt           # LLM format
│   │   ├── *_analysis.json     # Statistics
│   │   ├── *_report.json       # Processing metadata
│   │   ├── summaries/          # Summary outputs
│   │   │   ├── *_summary.txt
│   │   │   ├── *_summary.md
│   │   │   └── *_summary.json
│   │   └── handbooks/          # AI-generated handbooks (if enabled)
│   │       ├── *_user-guide.md
│   │       ├── *_technical-doc.md
│   │       └── *_faq-handbook.md
│   └── temp/                    # Temporary canonical files
│
└── Runtime Data
    ├── .cache/                  # Result cache (SHA256-based)
    ├── batch_progress.json      # Batch progress tracking
    ├── benchmark_results.json   # Performance benchmark results
    └── transcriptor.log         # Application logs
```

## 💡 Example Workflows

### Example 1: Single Meeting Recording

```bash
# 1. Add recording
cp meeting-2025-10-03.m4a ingestion/

# 2. Transcribe
python app.py process ingestion/meeting-2025-10-03.m4a

# 3. View transcription
cat output/meeting-2025-10-03_final.txt

# 4. Generate summary
python generate_summaries.py

# 5. View summary with key points
cat output/summaries/meeting-2025-10-03_summary.md
```

**Output files:**
- `meeting-2025-10-03_final.txt` - Full transcription
- `meeting-2025-10-03_final.srt` - Subtitles
- `meeting-2025-10-03_semantic.md` - LLM-ready format
- `meeting-2025-10-03_summary.md` - Summary with key points

### Example 2: Batch of Interviews

```bash
# 1. Add all interviews
cp interview*.m4a ingestion/

# 2. Start batch processing
python batch_process.py

# (Wait for completion or monitor with check_progress.py)

# 3. Generate summaries
python generate_summaries.py

# 4. Review all summaries
ls output/summaries/
```

### Example 3: Quick Preview

```bash
# Fast preview without full transcription
python app.py preview ingestion/audio.m4a

# View result in seconds
cat output/audio_preview.txt
```

### Example 4: Different Language

```bash
# Edit config.json first
# Set "language": "es" for Spanish

# Process Spanish audio
python app.py process ingestion/spanish-audio.m4a
```

See [User Guide - Basic Workflows](../../../docs/USER_GUIDE.md#basic-workflows) for more examples.

---

## ⚙️ Performance

### Processing Times

| Audio Length | Model | CPU | GPU |
|--------------|-------|-----|-----|
| 5 min | SMALL | 1.5 min | 0.3 min |
| 30 min | MEDIUM | 15 min | 3 min |
| 60 min | LARGE | 60 min | 12 min |

### Performance Optimizations (Phase 4)

**Result Caching:**
- Cache hit: ~1-10ms retrieval time
- Cache miss: Full transcription time
- Speedup: **100-1000x for repeated files**

**Parallel Batch Processing:**
- 2 workers: **~2x speedup**
- 4 workers: **~4x speedup**
- Actual speedup depends on CPU cores

**Memory Optimization:**
- Explicit garbage collection after model cleanup
- Prevents memory leaks in long-running batch jobs

**Benchmark Results:**
Run `python benchmark.py test_audio.wav` to measure performance on your system.

### Optimization Tips

**Speed:**
- Enable GPU (`device: "cuda"`)
- Enable result caching (`enable_cache: true`)
- Use parallel batch processing (edit batch_process.py)
- Use smaller models (SMALL/TINY)
- Disable noise reduction

**Quality:**
- Use larger models (MEDIUM/LARGE)
- Enable preprocessing
- Use high-quality audio files
- Specify correct language

**Batch Processing:**
- Enable parallel processing for 2-4x speedup
- Monitor progress with tqdm progress bars
- Resume capability handles interruptions

See [Performance Guide](../../../docs/PERFORMANCE.md) for detailed tuning and [Configuration Reference](../../../docs/CONFIGURATION.md#configuration-presets) for presets.

---

## 🔧 Troubleshooting

| Issue | Quick Fix |
|-------|-----------|
| FFmpeg not found | Install FFmpeg and add to PATH |
| Out of memory | Use smaller model in config.json |
| Slow processing | Enable GPU or use smaller model |
| Poor quality | Use larger model or check language |
| Batch stuck | Check progress with `check_progress.py` |

**See [Troubleshooting Guide](../../../docs/TROUBLESHOOTING.md) for detailed solutions**

---

## 📖 Documentation

**New user?** → [Quick Start Guide](../../../docs/QUICK_START.md)

**All documentation:** → [docs/README.md](../../../docs/README.md)

**Need help?** → [Troubleshooting Guide](../../../docs/TROUBLESHOOTING.md)

---

## 🎓 Learning Path

1. **Install** → [Quick Start - Installation](../../../docs/QUICK_START.md#installation)
2. **First transcription** → [Quick Start - First Transcription](../../../docs/QUICK_START.md#first-transcription-3-steps)
3. **Batch processing** → [User Guide - Batch Processing](../../../docs/USER_GUIDE.md#workflow-2-batch-processing)
4. **Generate summaries** → [User Guide - Generate Summaries](../../../docs/USER_GUIDE.md#workflow-3-generate-summaries)
5. **Customize** → [Configuration Reference](../../../docs/CONFIGURATION.md)
6. **Advanced** → [User Guide - Advanced Usage](../../../docs/USER_GUIDE.md#advanced-usage)

---

## 🌟 Key Highlights

✅ **10+ audio formats** supported (M4A, MP3, WAV, FLAC, OGG, etc.)
✅ **99 languages** via OpenAI Whisper
✅ **Automatic model selection** based on audio characteristics
✅ **Batch processing** with resume capability and parallel support
✅ **Multiple outputs**: TXT, SRT, JSON, Markdown, Summaries, AI Handbooks
✅ **AI-powered handbooks** using SmolLM2 (User Guides, Technical Docs, FAQ)
✅ **LLM-ready** formatting and semantic processing
✅ **Intelligent summaries** with key points extraction
✅ **Result caching** with SHA256 + TTL (100-1000x speedup)
✅ **GPU acceleration** for 5-10x speed boost
✅ **Complete documentation** with guides and references

---

## 📝 License

This project uses OpenAI's Whisper model. Please refer to Whisper's license terms.

---

## 🚀 Get Started

**Ready to transcribe?**

```bash
# 1. Install
pip install -r requirements.txt

# 2. Add audio
cp your-audio.m4a ingestion/

# 3. Transcribe
python app.py process ingestion/your-audio.m4a

# 4. View result
cat output/your-audio_final.txt
```

**Need help?** Start with [Quick Start Guide](../../../docs/QUICK_START.md)

**Happy Transcribing! 🎉**
