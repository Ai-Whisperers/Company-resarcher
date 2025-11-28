"""
Model Quantization support for running models efficiently.

Provides infrastructure for loading and running quantized models with
lower precision (4-bit, 8-bit) to save memory and increase speed.
"""

import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from .logger import setup_logger

logger = setup_logger("quantization")


class QuantizationType(str, Enum):
    """Supported quantization types."""

    NONE = "none"  # Full precision (fp32/fp16)
    INT8 = "int8"  # 8-bit quantization
    INT4 = "int4"  # 4-bit quantization
    NF4 = "nf4"  # 4-bit NormalFloat
    FP4 = "fp4"  # 4-bit Float
    GPTQ = "gptq"  # GPTQ quantization
    AWQ = "awq"  # Activation-aware Weight Quantization
    GGUF = "gguf"  # GGUF format (llama.cpp)


class ComputeType(str, Enum):
    """Compute precision types."""

    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    INT8 = "int8"
    INT4 = "int4"


@dataclass
class QuantizationConfig:
    """Configuration for model quantization."""

    # Quantization type
    quant_type: QuantizationType = QuantizationType.NONE

    # Precision settings
    compute_dtype: ComputeType = ComputeType.FP16
    use_double_quant: bool = True

    # 4-bit specific
    bnb_4bit_quant_type: str = "nf4"  # nf4 or fp4
    bnb_4bit_use_double_quant: bool = True
    bnb_4bit_compute_dtype: str = "float16"

    # 8-bit specific
    llm_int8_threshold: float = 6.0
    llm_int8_skip_modules: List[str] = field(default_factory=list)
    llm_int8_enable_fp32_cpu_offload: bool = False
    llm_int8_has_fp16_weight: bool = False

    # GPTQ specific
    gptq_bits: int = 4
    gptq_group_size: int = 128
    gptq_desc_act: bool = False
    gptq_sym: bool = True

    # AWQ specific
    awq_bits: int = 4
    awq_group_size: int = 128
    awq_zero_point: bool = True

    # GGUF specific
    gguf_file: Optional[str] = None
    n_gpu_layers: int = -1  # -1 = all layers on GPU
    n_ctx: int = 4096

    # Memory management
    max_memory: Optional[Dict[str, str]] = None
    device_map: str = "auto"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "quant_type": self.quant_type.value,
            "compute_dtype": self.compute_dtype.value,
            "use_double_quant": self.use_double_quant,
            "bnb_4bit_quant_type": self.bnb_4bit_quant_type,
            "bnb_4bit_use_double_quant": self.bnb_4bit_use_double_quant,
            "bnb_4bit_compute_dtype": self.bnb_4bit_compute_dtype,
            "llm_int8_threshold": self.llm_int8_threshold,
            "llm_int8_skip_modules": self.llm_int8_skip_modules,
            "gptq_bits": self.gptq_bits,
            "gptq_group_size": self.gptq_group_size,
            "awq_bits": self.awq_bits,
            "awq_group_size": self.awq_group_size,
            "gguf_file": self.gguf_file,
            "n_gpu_layers": self.n_gpu_layers,
            "n_ctx": self.n_ctx,
            "max_memory": self.max_memory,
            "device_map": self.device_map,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuantizationConfig":
        """Create from dictionary."""
        if "quant_type" in data:
            data["quant_type"] = QuantizationType(data["quant_type"])
        if "compute_dtype" in data:
            data["compute_dtype"] = ComputeType(data["compute_dtype"])

        valid_fields = {
            k: v for k, v in data.items()
            if hasattr(cls, k) or k in cls.__dataclass_fields__
        }
        return cls(**valid_fields)

    @classmethod
    def for_4bit(cls, double_quant: bool = True) -> "QuantizationConfig":
        """Create config for 4-bit quantization."""
        return cls(
            quant_type=QuantizationType.INT4,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=double_quant,
        )

    @classmethod
    def for_8bit(cls) -> "QuantizationConfig":
        """Create config for 8-bit quantization."""
        return cls(quant_type=QuantizationType.INT8)

    @classmethod
    def for_gptq(cls, bits: int = 4, group_size: int = 128) -> "QuantizationConfig":
        """Create config for GPTQ quantization."""
        return cls(
            quant_type=QuantizationType.GPTQ,
            gptq_bits=bits,
            gptq_group_size=group_size,
        )

    @classmethod
    def for_awq(cls, bits: int = 4, group_size: int = 128) -> "QuantizationConfig":
        """Create config for AWQ quantization."""
        return cls(
            quant_type=QuantizationType.AWQ,
            awq_bits=bits,
            awq_group_size=group_size,
        )

    @classmethod
    def for_gguf(cls, file_path: str, n_gpu_layers: int = -1) -> "QuantizationConfig":
        """Create config for GGUF model."""
        return cls(
            quant_type=QuantizationType.GGUF,
            gguf_file=file_path,
            n_gpu_layers=n_gpu_layers,
        )


@dataclass
class QuantizedModel:
    """Represents a loaded quantized model."""

    model_id: str
    config: QuantizationConfig
    model: Any = None  # Actual model object

    # Model info
    model_path: Optional[str] = None
    model_size_bytes: int = 0
    original_size_bytes: int = 0

    # Status
    is_loaded: bool = False
    error_message: Optional[str] = None

    @property
    def compression_ratio(self) -> float:
        """Calculate compression ratio."""
        if self.original_size_bytes == 0:
            return 1.0
        return self.model_size_bytes / self.original_size_bytes

    @property
    def memory_saved_percent(self) -> float:
        """Calculate memory saved percentage."""
        return (1.0 - self.compression_ratio) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_id": self.model_id,
            "config": self.config.to_dict(),
            "model_path": self.model_path,
            "model_size_bytes": self.model_size_bytes,
            "original_size_bytes": self.original_size_bytes,
            "compression_ratio": round(self.compression_ratio, 4),
            "memory_saved_percent": round(self.memory_saved_percent, 2),
            "is_loaded": self.is_loaded,
            "error_message": self.error_message,
        }


class ModelQuantizer:
    """
    Handles model quantization and loading.

    Supports multiple quantization methods including BitsAndBytes,
    GPTQ, AWQ, and GGUF formats.
    """

    def __init__(self):
        """Initialize the quantizer."""
        self._loaded_models: Dict[str, QuantizedModel] = {}
        self._lock = threading.Lock()

    def _estimate_original_size(self, model_path: str, param_count: int = 0) -> int:
        """Estimate original model size in bytes."""
        if param_count > 0:
            # FP16 = 2 bytes per param
            return param_count * 2

        # Rough estimates based on model name
        model_name = Path(model_path).name.lower()

        if "7b" in model_name:
            return 14_000_000_000  # ~14GB for 7B model in FP16
        elif "13b" in model_name:
            return 26_000_000_000
        elif "30b" in model_name or "33b" in model_name:
            return 66_000_000_000
        elif "65b" in model_name or "70b" in model_name:
            return 140_000_000_000
        else:
            return 0

    def _estimate_quantized_size(
        self,
        original_size: int,
        quant_type: QuantizationType,
    ) -> int:
        """Estimate quantized model size."""
        ratios = {
            QuantizationType.NONE: 1.0,
            QuantizationType.INT8: 0.5,
            QuantizationType.INT4: 0.25,
            QuantizationType.NF4: 0.25,
            QuantizationType.FP4: 0.25,
            QuantizationType.GPTQ: 0.25,
            QuantizationType.AWQ: 0.25,
            QuantizationType.GGUF: 0.25,  # Varies based on actual quantization
        }
        return int(original_size * ratios.get(quant_type, 1.0))

    def get_bitsandbytes_config(
        self,
        config: QuantizationConfig,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate BitsAndBytes configuration.

        Returns config dict compatible with transformers BitsAndBytesConfig.
        """
        if config.quant_type == QuantizationType.INT4:
            return {
                "load_in_4bit": True,
                "bnb_4bit_quant_type": config.bnb_4bit_quant_type,
                "bnb_4bit_use_double_quant": config.bnb_4bit_use_double_quant,
                "bnb_4bit_compute_dtype": config.bnb_4bit_compute_dtype,
            }
        elif config.quant_type == QuantizationType.INT8:
            return {
                "load_in_8bit": True,
                "llm_int8_threshold": config.llm_int8_threshold,
                "llm_int8_skip_modules": config.llm_int8_skip_modules or None,
                "llm_int8_enable_fp32_cpu_offload": config.llm_int8_enable_fp32_cpu_offload,
                "llm_int8_has_fp16_weight": config.llm_int8_has_fp16_weight,
            }
        return None

    def get_gptq_config(
        self,
        config: QuantizationConfig,
    ) -> Optional[Dict[str, Any]]:
        """Generate GPTQ configuration."""
        if config.quant_type != QuantizationType.GPTQ:
            return None

        return {
            "bits": config.gptq_bits,
            "group_size": config.gptq_group_size,
            "desc_act": config.gptq_desc_act,
            "sym": config.gptq_sym,
        }

    def get_awq_config(
        self,
        config: QuantizationConfig,
    ) -> Optional[Dict[str, Any]]:
        """Generate AWQ configuration."""
        if config.quant_type != QuantizationType.AWQ:
            return None

        return {
            "bits": config.awq_bits,
            "group_size": config.awq_group_size,
            "zero_point": config.awq_zero_point,
        }

    def get_gguf_config(
        self,
        config: QuantizationConfig,
    ) -> Optional[Dict[str, Any]]:
        """Generate GGUF/llama.cpp configuration."""
        if config.quant_type != QuantizationType.GGUF:
            return None

        return {
            "model_path": config.gguf_file,
            "n_gpu_layers": config.n_gpu_layers,
            "n_ctx": config.n_ctx,
        }

    def load_model(
        self,
        model_path: str,
        config: QuantizationConfig,
        model_id: Optional[str] = None,
        loader_fn: Optional[Callable[[str, Dict[str, Any]], Any]] = None,
    ) -> QuantizedModel:
        """
        Load a quantized model.

        Args:
            model_path: Path or HuggingFace model ID.
            config: Quantization configuration.
            model_id: Optional unique ID for this model.
            loader_fn: Optional custom loader function.

        Returns:
            QuantizedModel instance.
        """
        model_id = model_id or f"model_{len(self._loaded_models)}"

        # Estimate sizes
        original_size = self._estimate_original_size(model_path)
        quantized_size = self._estimate_quantized_size(original_size, config.quant_type)

        qmodel = QuantizedModel(
            model_id=model_id,
            config=config,
            model_path=model_path,
            original_size_bytes=original_size,
            model_size_bytes=quantized_size,
        )

        try:
            if loader_fn:
                # Use custom loader
                load_config = self._get_load_config(config)
                qmodel.model = loader_fn(model_path, load_config)
            else:
                # Simulate loading (actual loading requires transformers/llama-cpp)
                logger.info(
                    f"Simulated loading {model_path} with {config.quant_type.value} quantization"
                )
                qmodel.model = {"path": model_path, "config": config.to_dict()}

            qmodel.is_loaded = True

            with self._lock:
                self._loaded_models[model_id] = qmodel

            logger.info(f"Loaded model {model_id} ({config.quant_type.value})")

        except Exception as e:
            qmodel.error_message = str(e)
            logger.error(f"Failed to load model: {e}")

        return qmodel

    def _get_load_config(self, config: QuantizationConfig) -> Dict[str, Any]:
        """Get loading configuration based on quantization type."""
        if config.quant_type in (QuantizationType.INT4, QuantizationType.INT8):
            return self.get_bitsandbytes_config(config) or {}
        elif config.quant_type == QuantizationType.GPTQ:
            return self.get_gptq_config(config) or {}
        elif config.quant_type == QuantizationType.AWQ:
            return self.get_awq_config(config) or {}
        elif config.quant_type == QuantizationType.GGUF:
            return self.get_gguf_config(config) or {}
        return {}

    def get_model(self, model_id: str) -> Optional[QuantizedModel]:
        """Get a loaded model by ID."""
        return self._loaded_models.get(model_id)

    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory."""
        with self._lock:
            if model_id in self._loaded_models:
                qmodel = self._loaded_models[model_id]
                qmodel.model = None
                qmodel.is_loaded = False
                del self._loaded_models[model_id]
                logger.info(f"Unloaded model {model_id}")
                return True
        return False

    def list_models(self) -> List[QuantizedModel]:
        """List all loaded models."""
        return list(self._loaded_models.values())

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get total memory usage of loaded models."""
        total_quantized = sum(m.model_size_bytes for m in self._loaded_models.values())
        total_original = sum(m.original_size_bytes for m in self._loaded_models.values())

        return {
            "models_loaded": len(self._loaded_models),
            "total_quantized_bytes": total_quantized,
            "total_original_bytes": total_original,
            "memory_saved_bytes": total_original - total_quantized,
            "memory_saved_percent": (
                (1 - total_quantized / total_original) * 100
                if total_original > 0 else 0
            ),
        }


class QuantizationPresets:
    """Predefined quantization configurations for common use cases."""

    @staticmethod
    def memory_efficient() -> QuantizationConfig:
        """Maximum memory savings with 4-bit quantization."""
        return QuantizationConfig.for_4bit(double_quant=True)

    @staticmethod
    def balanced() -> QuantizationConfig:
        """Balance between quality and memory with 8-bit."""
        return QuantizationConfig.for_8bit()

    @staticmethod
    def high_quality() -> QuantizationConfig:
        """Higher quality GPTQ quantization."""
        return QuantizationConfig.for_gptq(bits=4, group_size=128)

    @staticmethod
    def fastest() -> QuantizationConfig:
        """Fastest inference with AWQ."""
        return QuantizationConfig.for_awq(bits=4, group_size=128)

    @staticmethod
    def cpu_friendly(gguf_path: str) -> QuantizationConfig:
        """CPU-optimized with GGUF format."""
        return QuantizationConfig.for_gguf(gguf_path, n_gpu_layers=0)

    @staticmethod
    def gpu_offload(gguf_path: str, layers: int = -1) -> QuantizationConfig:
        """GGUF with GPU layer offloading."""
        return QuantizationConfig.for_gguf(gguf_path, n_gpu_layers=layers)


def get_recommended_config(
    model_size: str,
    available_vram_gb: float,
    prefer_quality: bool = False,
) -> QuantizationConfig:
    """
    Get recommended quantization config based on hardware.

    Args:
        model_size: Model size string (e.g., "7b", "13b", "70b").
        available_vram_gb: Available GPU VRAM in GB.
        prefer_quality: Prefer quality over memory savings.

    Returns:
        Recommended QuantizationConfig.
    """
    model_size = model_size.lower()

    # Size requirements in GB (approximate for FP16)
    size_requirements = {
        "1b": 2,
        "3b": 6,
        "7b": 14,
        "13b": 26,
        "30b": 60,
        "33b": 66,
        "65b": 130,
        "70b": 140,
    }

    # Parse model size
    required_vram = 0
    for size_key, vram in size_requirements.items():
        if size_key in model_size:
            required_vram = vram
            break

    if required_vram == 0:
        # Unknown size, assume medium
        required_vram = 14

    # 4-bit reduces to ~1/4
    required_4bit = required_vram / 4
    # 8-bit reduces to ~1/2
    required_8bit = required_vram / 2

    if available_vram_gb >= required_vram:
        # Enough for full precision
        if prefer_quality:
            return QuantizationConfig()  # No quantization
        return QuantizationConfig.for_8bit()

    elif available_vram_gb >= required_8bit:
        # Enough for 8-bit
        return QuantizationConfig.for_8bit()

    elif available_vram_gb >= required_4bit:
        # Need 4-bit
        if prefer_quality:
            return QuantizationPresets.high_quality()  # GPTQ
        return QuantizationPresets.memory_efficient()  # BnB 4-bit

    else:
        # Very limited VRAM, recommend CPU offload
        return QuantizationConfig(
            quant_type=QuantizationType.INT4,
            bnb_4bit_use_double_quant=True,
            llm_int8_enable_fp32_cpu_offload=True,
        )


# Global instance
_quantizer: Optional[ModelQuantizer] = None
_global_lock = threading.Lock()


def get_quantizer() -> ModelQuantizer:
    """Get or create the global quantizer."""
    global _quantizer
    with _global_lock:
        if _quantizer is None:
            _quantizer = ModelQuantizer()
        return _quantizer


def reset_quantizer() -> None:
    """Reset the global quantizer (for testing)."""
    global _quantizer
    with _global_lock:
        _quantizer = None
