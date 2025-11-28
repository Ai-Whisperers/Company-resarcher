"""Tests for the model quantization system."""

import pytest

from src.core.quantization import (
    ComputeType,
    ModelQuantizer,
    QuantizationConfig,
    QuantizationPresets,
    QuantizationType,
    QuantizedModel,
    get_quantizer,
    get_recommended_config,
    reset_quantizer,
)


class TestQuantizationConfig:
    """Tests for QuantizationConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = QuantizationConfig()

        assert config.quant_type == QuantizationType.NONE
        assert config.compute_dtype == ComputeType.FP16
        assert config.use_double_quant is True

    def test_for_4bit(self):
        """Test 4-bit configuration factory."""
        config = QuantizationConfig.for_4bit()

        assert config.quant_type == QuantizationType.INT4
        assert config.bnb_4bit_quant_type == "nf4"
        assert config.bnb_4bit_use_double_quant is True

    def test_for_4bit_no_double_quant(self):
        """Test 4-bit without double quantization."""
        config = QuantizationConfig.for_4bit(double_quant=False)

        assert config.bnb_4bit_use_double_quant is False

    def test_for_8bit(self):
        """Test 8-bit configuration factory."""
        config = QuantizationConfig.for_8bit()

        assert config.quant_type == QuantizationType.INT8

    def test_for_gptq(self):
        """Test GPTQ configuration factory."""
        config = QuantizationConfig.for_gptq(bits=4, group_size=64)

        assert config.quant_type == QuantizationType.GPTQ
        assert config.gptq_bits == 4
        assert config.gptq_group_size == 64

    def test_for_awq(self):
        """Test AWQ configuration factory."""
        config = QuantizationConfig.for_awq(bits=4, group_size=128)

        assert config.quant_type == QuantizationType.AWQ
        assert config.awq_bits == 4
        assert config.awq_group_size == 128

    def test_for_gguf(self):
        """Test GGUF configuration factory."""
        config = QuantizationConfig.for_gguf(
            file_path="/path/model.gguf",
            n_gpu_layers=20,
        )

        assert config.quant_type == QuantizationType.GGUF
        assert config.gguf_file == "/path/model.gguf"
        assert config.n_gpu_layers == 20

    def test_to_dict(self):
        """Test serialization."""
        config = QuantizationConfig.for_4bit()
        data = config.to_dict()

        assert data["quant_type"] == "int4"
        assert data["bnb_4bit_quant_type"] == "nf4"

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "quant_type": "int8",
            "llm_int8_threshold": 5.0,
        }
        config = QuantizationConfig.from_dict(data)

        assert config.quant_type == QuantizationType.INT8
        assert config.llm_int8_threshold == 5.0


class TestQuantizedModel:
    """Tests for QuantizedModel class."""

    def test_create_model(self):
        """Test creating a quantized model."""
        config = QuantizationConfig.for_4bit()
        model = QuantizedModel(
            model_id="test_model",
            config=config,
            model_path="/path/to/model",
        )

        assert model.model_id == "test_model"
        assert model.is_loaded is False

    def test_compression_ratio(self):
        """Test compression ratio calculation."""
        config = QuantizationConfig.for_4bit()
        model = QuantizedModel(
            model_id="test",
            config=config,
            original_size_bytes=1000,
            model_size_bytes=250,
        )

        assert model.compression_ratio == 0.25
        assert model.memory_saved_percent == 75.0

    def test_compression_ratio_no_original(self):
        """Test compression ratio with no original size."""
        config = QuantizationConfig()
        model = QuantizedModel(
            model_id="test",
            config=config,
        )

        assert model.compression_ratio == 1.0

    def test_to_dict(self):
        """Test serialization."""
        config = QuantizationConfig.for_4bit()
        model = QuantizedModel(
            model_id="test",
            config=config,
            model_path="/path/model",
            original_size_bytes=1000,
            model_size_bytes=250,
            is_loaded=True,
        )
        data = model.to_dict()

        assert data["model_id"] == "test"
        assert data["compression_ratio"] == 0.25
        assert data["memory_saved_percent"] == 75.0
        assert data["is_loaded"] is True


class TestModelQuantizer:
    """Tests for ModelQuantizer class."""

    def setup_method(self):
        """Create quantizer."""
        self.quantizer = ModelQuantizer()

    def test_get_bitsandbytes_config_4bit(self):
        """Test BnB config for 4-bit."""
        config = QuantizationConfig.for_4bit()
        bnb_config = self.quantizer.get_bitsandbytes_config(config)

        assert bnb_config is not None
        assert bnb_config["load_in_4bit"] is True
        assert bnb_config["bnb_4bit_quant_type"] == "nf4"

    def test_get_bitsandbytes_config_8bit(self):
        """Test BnB config for 8-bit."""
        config = QuantizationConfig.for_8bit()
        bnb_config = self.quantizer.get_bitsandbytes_config(config)

        assert bnb_config is not None
        assert bnb_config["load_in_8bit"] is True

    def test_get_bitsandbytes_config_none(self):
        """Test BnB config for non-BnB quantization."""
        config = QuantizationConfig.for_gptq()
        bnb_config = self.quantizer.get_bitsandbytes_config(config)

        assert bnb_config is None

    def test_get_gptq_config(self):
        """Test GPTQ config generation."""
        config = QuantizationConfig.for_gptq(bits=4, group_size=64)
        gptq_config = self.quantizer.get_gptq_config(config)

        assert gptq_config is not None
        assert gptq_config["bits"] == 4
        assert gptq_config["group_size"] == 64

    def test_get_awq_config(self):
        """Test AWQ config generation."""
        config = QuantizationConfig.for_awq()
        awq_config = self.quantizer.get_awq_config(config)

        assert awq_config is not None
        assert "bits" in awq_config
        assert "group_size" in awq_config

    def test_get_gguf_config(self):
        """Test GGUF config generation."""
        config = QuantizationConfig.for_gguf("/model.gguf", n_gpu_layers=10)
        gguf_config = self.quantizer.get_gguf_config(config)

        assert gguf_config is not None
        assert gguf_config["model_path"] == "/model.gguf"
        assert gguf_config["n_gpu_layers"] == 10

    def test_load_model(self):
        """Test loading a model (simulated)."""
        config = QuantizationConfig.for_4bit()
        model = self.quantizer.load_model(
            model_path="test/model-7b",
            config=config,
            model_id="test_7b",
        )

        assert model.model_id == "test_7b"
        assert model.is_loaded is True

    def test_load_model_with_custom_loader(self):
        """Test loading with custom loader."""
        config = QuantizationConfig.for_4bit()

        def custom_loader(path, load_config):
            return {"loaded_from": path, "config": load_config}

        model = self.quantizer.load_model(
            model_path="test/model",
            config=config,
            loader_fn=custom_loader,
        )

        assert model.is_loaded is True
        assert model.model["loaded_from"] == "test/model"

    def test_get_model(self):
        """Test getting a loaded model."""
        config = QuantizationConfig.for_4bit()
        self.quantizer.load_model(
            model_path="test/model",
            config=config,
            model_id="my_model",
        )

        model = self.quantizer.get_model("my_model")
        assert model is not None
        assert model.model_id == "my_model"

    def test_get_model_not_found(self):
        """Test getting non-existent model."""
        model = self.quantizer.get_model("nonexistent")
        assert model is None

    def test_unload_model(self):
        """Test unloading a model."""
        config = QuantizationConfig.for_4bit()
        self.quantizer.load_model(
            model_path="test/model",
            config=config,
            model_id="to_unload",
        )

        success = self.quantizer.unload_model("to_unload")
        assert success is True

        model = self.quantizer.get_model("to_unload")
        assert model is None

    def test_list_models(self):
        """Test listing loaded models."""
        config = QuantizationConfig.for_4bit()

        for i in range(3):
            self.quantizer.load_model(
                model_path=f"test/model_{i}",
                config=config,
                model_id=f"model_{i}",
            )

        models = self.quantizer.list_models()
        assert len(models) == 3

    def test_get_memory_usage(self):
        """Test getting memory usage."""
        config = QuantizationConfig.for_4bit()
        self.quantizer.load_model(
            model_path="test/model-7b",
            config=config,
        )

        usage = self.quantizer.get_memory_usage()

        assert usage["models_loaded"] == 1
        assert "total_quantized_bytes" in usage
        assert "memory_saved_percent" in usage


class TestQuantizationPresets:
    """Tests for QuantizationPresets class."""

    def test_memory_efficient(self):
        """Test memory efficient preset."""
        config = QuantizationPresets.memory_efficient()

        assert config.quant_type == QuantizationType.INT4
        assert config.bnb_4bit_use_double_quant is True

    def test_balanced(self):
        """Test balanced preset."""
        config = QuantizationPresets.balanced()

        assert config.quant_type == QuantizationType.INT8

    def test_high_quality(self):
        """Test high quality preset."""
        config = QuantizationPresets.high_quality()

        assert config.quant_type == QuantizationType.GPTQ

    def test_fastest(self):
        """Test fastest preset."""
        config = QuantizationPresets.fastest()

        assert config.quant_type == QuantizationType.AWQ

    def test_cpu_friendly(self):
        """Test CPU friendly preset."""
        config = QuantizationPresets.cpu_friendly("/model.gguf")

        assert config.quant_type == QuantizationType.GGUF
        assert config.n_gpu_layers == 0

    def test_gpu_offload(self):
        """Test GPU offload preset."""
        config = QuantizationPresets.gpu_offload("/model.gguf", layers=20)

        assert config.quant_type == QuantizationType.GGUF
        assert config.n_gpu_layers == 20


class TestGetRecommendedConfig:
    """Tests for get_recommended_config function."""

    def test_recommend_for_7b_high_vram(self):
        """Test recommendation for 7B model with high VRAM."""
        config = get_recommended_config("7b", available_vram_gb=24)

        # Should recommend 8-bit or better
        assert config.quant_type in (
            QuantizationType.NONE,
            QuantizationType.INT8,
        )

    def test_recommend_for_7b_medium_vram(self):
        """Test recommendation for 7B model with medium VRAM."""
        config = get_recommended_config("7b", available_vram_gb=8)

        # Should recommend 8-bit
        assert config.quant_type == QuantizationType.INT8

    def test_recommend_for_7b_low_vram(self):
        """Test recommendation for 7B model with low VRAM."""
        config = get_recommended_config("7b", available_vram_gb=4)

        # Should recommend 4-bit
        assert config.quant_type in (
            QuantizationType.INT4,
            QuantizationType.GPTQ,
        )

    def test_recommend_for_70b_low_vram(self):
        """Test recommendation for 70B model with low VRAM."""
        config = get_recommended_config("70b", available_vram_gb=24)

        # Should recommend aggressive quantization
        assert config.quant_type == QuantizationType.INT4

    def test_recommend_prefer_quality(self):
        """Test recommendation with quality preference."""
        config = get_recommended_config(
            "7b",
            available_vram_gb=4,
            prefer_quality=True,
        )

        # Should recommend GPTQ for quality
        assert config.quant_type == QuantizationType.GPTQ

    def test_recommend_unknown_size(self):
        """Test recommendation for unknown model size."""
        config = get_recommended_config("custom-model", available_vram_gb=8)

        # Should return some valid config
        assert config.quant_type is not None


class TestGlobalFunctions:
    """Tests for global functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_quantizer()

    def teardown_method(self):
        """Reset after each test."""
        reset_quantizer()

    def test_get_quantizer_singleton(self):
        """Test singleton behavior."""
        q1 = get_quantizer()
        q2 = get_quantizer()
        assert q1 is q2

    def test_reset_quantizer(self):
        """Test resetting singleton."""
        q1 = get_quantizer()
        reset_quantizer()
        q2 = get_quantizer()
        assert q1 is not q2


class TestQuantizationTypes:
    """Tests for quantization type enums."""

    def test_all_quant_types(self):
        """Test all quantization types are defined."""
        types = [
            QuantizationType.NONE,
            QuantizationType.INT8,
            QuantizationType.INT4,
            QuantizationType.NF4,
            QuantizationType.FP4,
            QuantizationType.GPTQ,
            QuantizationType.AWQ,
            QuantizationType.GGUF,
        ]
        assert len(types) == len(QuantizationType)

    def test_compute_types(self):
        """Test all compute types are defined."""
        types = [
            ComputeType.FP32,
            ComputeType.FP16,
            ComputeType.BF16,
            ComputeType.INT8,
            ComputeType.INT4,
        ]
        assert len(types) == len(ComputeType)

    def test_type_values(self):
        """Test type values are strings."""
        assert QuantizationType.INT4.value == "int4"
        assert ComputeType.FP16.value == "fp16"
