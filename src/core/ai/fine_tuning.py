"""
Fine-tuning Pipeline for Custom Model Training.

Provides infrastructure for collecting training data, managing fine-tuning
jobs, and integrating fine-tuned models back into the system.
"""

import asyncio
import hashlib
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from ..logging import setup_logger

logger = setup_logger("fine_tuning")


class DatasetFormat(str, Enum):
    """Supported dataset formats."""

    ALPACA = "alpaca"  # instruction, input, output
    SHAREGPT = "sharegpt"  # conversations list
    OPENAI = "openai"  # messages format
    CUSTOM = "custom"


class TrainingStatus(str, Enum):
    """Training job status."""

    PENDING = "pending"
    PREPARING = "preparing"
    TRAINING = "training"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TrainingSample:
    """A single training sample (prompt-response pair)."""

    sample_id: str
    instruction: str
    input: str = ""
    output: str = ""
    system: Optional[str] = None

    # Metadata
    source: str = "agent"
    task_type: Optional[str] = None
    quality_score: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_alpaca(self) -> Dict[str, str]:
        """Convert to Alpaca format."""
        result = {
            "instruction": self.instruction,
            "input": self.input,
            "output": self.output,
        }
        if self.system:
            result["system"] = self.system
        return result

    def to_sharegpt(self) -> Dict[str, Any]:
        """Convert to ShareGPT format."""
        conversations = []
        if self.system:
            conversations.append({"from": "system", "value": self.system})

        # Combine instruction and input for user message
        user_msg = self.instruction
        if self.input:
            user_msg += f"\n\n{self.input}"

        conversations.append({"from": "human", "value": user_msg})
        conversations.append({"from": "gpt", "value": self.output})

        return {"conversations": conversations}

    def to_openai(self) -> Dict[str, Any]:
        """Convert to OpenAI messages format."""
        messages = []
        if self.system:
            messages.append({"role": "system", "content": self.system})

        user_msg = self.instruction
        if self.input:
            user_msg += f"\n\n{self.input}"

        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": self.output})

        return {"messages": messages}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sample_id": self.sample_id,
            "instruction": self.instruction,
            "input": self.input,
            "output": self.output,
            "system": self.system,
            "source": self.source,
            "task_type": self.task_type,
            "quality_score": self.quality_score,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrainingSample":
        """Create from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()

        return cls(
            sample_id=data["sample_id"],
            instruction=data["instruction"],
            input=data.get("input", ""),
            output=data.get("output", ""),
            system=data.get("system"),
            source=data.get("source", "agent"),
            task_type=data.get("task_type"),
            quality_score=data.get("quality_score"),
            created_at=created_at,
            metadata=data.get("metadata", {}),
        )


@dataclass
class TrainingConfig:
    """Configuration for a fine-tuning job."""

    # Model settings
    base_model: str = "meta-llama/Llama-3-8B"
    output_dir: str = "./output"

    # LoRA settings
    use_lora: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: List[str] = field(
        default_factory=lambda: ["q_proj", "v_proj", "k_proj", "o_proj"]
    )

    # Training settings
    num_epochs: int = 3
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    warmup_ratio: float = 0.03
    weight_decay: float = 0.01
    max_seq_length: int = 2048

    # Data settings
    train_split: float = 0.9
    shuffle: bool = True
    seed: int = 42

    # Evaluation
    eval_steps: int = 100
    save_steps: int = 100
    logging_steps: int = 10

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "base_model": self.base_model,
            "output_dir": self.output_dir,
            "use_lora": self.use_lora,
            "lora_r": self.lora_r,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": self.lora_dropout,
            "target_modules": self.target_modules,
            "num_epochs": self.num_epochs,
            "batch_size": self.batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "learning_rate": self.learning_rate,
            "warmup_ratio": self.warmup_ratio,
            "weight_decay": self.weight_decay,
            "max_seq_length": self.max_seq_length,
            "train_split": self.train_split,
            "shuffle": self.shuffle,
            "seed": self.seed,
            "eval_steps": self.eval_steps,
            "save_steps": self.save_steps,
            "logging_steps": self.logging_steps,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrainingConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class TrainingJob:
    """Represents a fine-tuning training job."""

    job_id: str
    config: TrainingConfig
    dataset_path: str
    status: TrainingStatus = TrainingStatus.PENDING

    # Progress tracking
    current_epoch: int = 0
    current_step: int = 0
    total_steps: int = 0

    # Metrics
    train_loss: Optional[float] = None
    eval_loss: Optional[float] = None
    metrics: Dict[str, float] = field(default_factory=dict)

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Output
    output_path: Optional[str] = None
    error_message: Optional[str] = None

    @property
    def progress(self) -> float:
        """Calculate training progress (0.0 to 1.0)."""
        if self.total_steps == 0:
            return 0.0
        return min(1.0, self.current_step / self.total_steps)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate job duration in seconds."""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "config": self.config.to_dict(),
            "dataset_path": self.dataset_path,
            "status": self.status.value,
            "current_epoch": self.current_epoch,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "train_loss": self.train_loss,
            "eval_loss": self.eval_loss,
            "metrics": self.metrics,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "output_path": self.output_path,
            "error_message": self.error_message,
            "progress": self.progress,
        }


class DatasetCollector:
    """
    Collects and manages training data from agent interactions.

    Stores successful prompt-response pairs for fine-tuning.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize the collector.

        Args:
            storage_path: Path to store collected samples.
        """
        self.storage_path = storage_path or Path("./training_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._samples: Dict[str, TrainingSample] = {}
        self._lock = threading.Lock()
        self._load_existing()

    def _load_existing(self) -> None:
        """Load existing samples from storage."""
        samples_file = self.storage_path / "samples.json"
        if samples_file.exists():
            try:
                data = json.loads(samples_file.read_text())
                for sample_data in data:
                    sample = TrainingSample.from_dict(sample_data)
                    self._samples[sample.sample_id] = sample
                logger.info(f"Loaded {len(self._samples)} existing samples")
            except Exception as e:
                logger.warning(f"Failed to load samples: {e}")

    def _save_samples(self) -> None:
        """Save samples to storage."""
        samples_file = self.storage_path / "samples.json"
        data = [s.to_dict() for s in self._samples.values()]
        samples_file.write_text(json.dumps(data, indent=2))

    def _generate_id(self, instruction: str, output: str) -> str:
        """Generate a unique sample ID."""
        content = f"{instruction}:{output}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def add_sample(
        self,
        instruction: str,
        output: str,
        input: str = "",
        system: Optional[str] = None,
        source: str = "agent",
        task_type: Optional[str] = None,
        quality_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TrainingSample:
        """
        Add a training sample.

        Args:
            instruction: The instruction/prompt.
            output: The expected response.
            input: Optional additional input context.
            system: Optional system prompt.
            source: Source of the sample.
            task_type: Type of task.
            quality_score: Quality score (0-1).
            metadata: Additional metadata.

        Returns:
            The created TrainingSample.
        """
        sample_id = self._generate_id(instruction, output)

        sample = TrainingSample(
            sample_id=sample_id,
            instruction=instruction,
            input=input,
            output=output,
            system=system,
            source=source,
            task_type=task_type,
            quality_score=quality_score,
            metadata=metadata or {},
        )

        with self._lock:
            self._samples[sample_id] = sample
            self._save_samples()

        logger.debug(f"Added sample {sample_id}")
        return sample

    def add_conversation(
        self,
        messages: List[Dict[str, str]],
        source: str = "agent",
        task_type: Optional[str] = None,
    ) -> List[TrainingSample]:
        """
        Add samples from a conversation.

        Args:
            messages: List of {"role": "user"|"assistant", "content": ...}.
            source: Source of the samples.
            task_type: Type of task.

        Returns:
            List of created samples.
        """
        samples = []
        system = None

        # Extract system message if present
        for msg in messages:
            if msg.get("role") == "system":
                system = msg.get("content", "")
                break

        # Create samples from user-assistant pairs
        pending_user = None
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")

            if role == "user":
                pending_user = content
            elif role == "assistant" and pending_user:
                sample = self.add_sample(
                    instruction=pending_user,
                    output=content,
                    system=system,
                    source=source,
                    task_type=task_type,
                )
                samples.append(sample)
                pending_user = None

        return samples

    def get_sample(self, sample_id: str) -> Optional[TrainingSample]:
        """Get a sample by ID."""
        return self._samples.get(sample_id)

    def list_samples(
        self,
        task_type: Optional[str] = None,
        min_quality: Optional[float] = None,
        source: Optional[str] = None,
    ) -> List[TrainingSample]:
        """
        List samples with optional filtering.

        Args:
            task_type: Filter by task type.
            min_quality: Minimum quality score.
            source: Filter by source.

        Returns:
            Filtered list of samples.
        """
        samples = list(self._samples.values())

        if task_type:
            samples = [s for s in samples if s.task_type == task_type]

        if min_quality is not None:
            samples = [
                s for s in samples
                if s.quality_score is not None and s.quality_score >= min_quality
            ]

        if source:
            samples = [s for s in samples if s.source == source]

        return samples

    def remove_sample(self, sample_id: str) -> bool:
        """Remove a sample."""
        with self._lock:
            if sample_id in self._samples:
                del self._samples[sample_id]
                self._save_samples()
                return True
        return False

    def update_quality(self, sample_id: str, score: float) -> bool:
        """Update a sample's quality score."""
        with self._lock:
            if sample_id in self._samples:
                self._samples[sample_id].quality_score = score
                self._save_samples()
                return True
        return False

    def export_dataset(
        self,
        output_path: Path,
        format: DatasetFormat = DatasetFormat.ALPACA,
        task_type: Optional[str] = None,
        min_quality: Optional[float] = None,
    ) -> int:
        """
        Export samples as a training dataset.

        Args:
            output_path: Path for the output file.
            format: Dataset format.
            task_type: Filter by task type.
            min_quality: Minimum quality score.

        Returns:
            Number of samples exported.
        """
        samples = self.list_samples(task_type=task_type, min_quality=min_quality)

        if format == DatasetFormat.ALPACA:
            data = [s.to_alpaca() for s in samples]
        elif format == DatasetFormat.SHAREGPT:
            data = [s.to_sharegpt() for s in samples]
        elif format == DatasetFormat.OPENAI:
            data = [s.to_openai() for s in samples]
        else:
            data = [s.to_dict() for s in samples]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, indent=2))

        logger.info(f"Exported {len(data)} samples to {output_path}")
        return len(data)

    @property
    def count(self) -> int:
        """Get total sample count."""
        return len(self._samples)

    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        samples = list(self._samples.values())

        if not samples:
            return {"total": 0}

        # Count by source
        by_source: Dict[str, int] = {}
        for s in samples:
            by_source[s.source] = by_source.get(s.source, 0) + 1

        # Count by task type
        by_task: Dict[str, int] = {}
        for s in samples:
            if s.task_type:
                by_task[s.task_type] = by_task.get(s.task_type, 0) + 1

        # Quality stats
        quality_scores = [s.quality_score for s in samples if s.quality_score is not None]

        return {
            "total": len(samples),
            "by_source": by_source,
            "by_task_type": by_task,
            "with_quality_score": len(quality_scores),
            "avg_quality": sum(quality_scores) / len(quality_scores) if quality_scores else None,
        }


class FineTuningPipeline:
    """
    Manages the fine-tuning pipeline.

    Handles dataset preparation, training execution, and model integration.
    """

    def __init__(
        self,
        collector: Optional[DatasetCollector] = None,
        output_dir: Optional[Path] = None,
    ):
        """
        Initialize the pipeline.

        Args:
            collector: Data collector instance.
            output_dir: Directory for output models.
        """
        self.collector = collector or DatasetCollector()
        self.output_dir = output_dir or Path("./fine_tuned_models")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._jobs: Dict[str, TrainingJob] = {}
        self._lock = threading.Lock()
        self._callbacks: List[Callable[[TrainingJob], None]] = []

    def _generate_job_id(self) -> str:
        """Generate a unique job ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"job_{timestamp}"

    def add_callback(self, callback: Callable[[TrainingJob], None]) -> None:
        """Add a status update callback."""
        self._callbacks.append(callback)

    def _notify_callbacks(self, job: TrainingJob) -> None:
        """Notify all callbacks of job update."""
        for callback in self._callbacks:
            try:
                callback(job)
            except Exception as e:
                logger.warning(f"Callback error: {e}")

    def prepare_dataset(
        self,
        output_name: str,
        format: DatasetFormat = DatasetFormat.ALPACA,
        task_type: Optional[str] = None,
        min_quality: Optional[float] = None,
        train_split: float = 0.9,
    ) -> Dict[str, Path]:
        """
        Prepare a dataset for training.

        Args:
            output_name: Name for the dataset files.
            format: Output format.
            task_type: Filter by task type.
            min_quality: Minimum quality score.
            train_split: Fraction for training set.

        Returns:
            Paths to train and eval dataset files.
        """
        import random

        samples = self.collector.list_samples(
            task_type=task_type,
            min_quality=min_quality,
        )

        if not samples:
            raise ValueError("No samples available for dataset")

        # Shuffle and split
        random.shuffle(samples)
        split_idx = int(len(samples) * train_split)
        train_samples = samples[:split_idx]
        eval_samples = samples[split_idx:]

        # Export datasets
        dataset_dir = self.output_dir / "datasets" / output_name
        dataset_dir.mkdir(parents=True, exist_ok=True)

        train_path = dataset_dir / "train.json"
        eval_path = dataset_dir / "eval.json"

        # Convert to format
        if format == DatasetFormat.ALPACA:
            train_data = [s.to_alpaca() for s in train_samples]
            eval_data = [s.to_alpaca() for s in eval_samples]
        elif format == DatasetFormat.SHAREGPT:
            train_data = [s.to_sharegpt() for s in train_samples]
            eval_data = [s.to_sharegpt() for s in eval_samples]
        else:
            train_data = [s.to_dict() for s in train_samples]
            eval_data = [s.to_dict() for s in eval_samples]

        train_path.write_text(json.dumps(train_data, indent=2))
        eval_path.write_text(json.dumps(eval_data, indent=2))

        logger.info(
            f"Prepared dataset: {len(train_samples)} train, {len(eval_samples)} eval"
        )

        return {"train": train_path, "eval": eval_path}

    def create_job(
        self,
        dataset_path: Union[str, Path],
        config: Optional[TrainingConfig] = None,
    ) -> TrainingJob:
        """
        Create a new training job.

        Args:
            dataset_path: Path to training dataset.
            config: Training configuration.

        Returns:
            The created TrainingJob.
        """
        job_id = self._generate_job_id()
        config = config or TrainingConfig()

        # Set output directory
        config.output_dir = str(self.output_dir / "checkpoints" / job_id)

        job = TrainingJob(
            job_id=job_id,
            config=config,
            dataset_path=str(dataset_path),
        )

        with self._lock:
            self._jobs[job_id] = job

        logger.info(f"Created training job {job_id}")
        return job

    def get_job(self, job_id: str) -> Optional[TrainingJob]:
        """Get a job by ID."""
        return self._jobs.get(job_id)

    def list_jobs(
        self,
        status: Optional[TrainingStatus] = None,
    ) -> List[TrainingJob]:
        """List jobs with optional status filter."""
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    async def run_job(
        self,
        job_id: str,
        trainer_callback: Optional[Callable[[TrainingJob], Any]] = None,
    ) -> TrainingJob:
        """
        Execute a training job.

        This is a simulation - actual training requires external libraries.

        Args:
            job_id: Job ID to run.
            trainer_callback: Optional callback to execute actual training.

        Returns:
            Updated TrainingJob.
        """
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.status != TrainingStatus.PENDING:
            raise ValueError(f"Job {job_id} is not pending")

        try:
            # Update status
            job.status = TrainingStatus.PREPARING
            job.started_at = datetime.now()
            self._notify_callbacks(job)

            # Simulate preparation
            await asyncio.sleep(0.1)

            # Start training
            job.status = TrainingStatus.TRAINING
            job.total_steps = job.config.num_epochs * 100  # Simulated
            self._notify_callbacks(job)

            if trainer_callback:
                # Use external trainer
                result = trainer_callback(job)
                if asyncio.iscoroutine(result):
                    await result
            else:
                # Simulate training progress
                for epoch in range(job.config.num_epochs):
                    job.current_epoch = epoch + 1
                    for step in range(100):
                        job.current_step = epoch * 100 + step + 1
                        job.train_loss = 2.0 / (job.current_step + 1)  # Decreasing loss
                        await asyncio.sleep(0.01)  # Simulate training time

                        if step % 10 == 0:
                            self._notify_callbacks(job)

            # Evaluation
            job.status = TrainingStatus.EVALUATING
            self._notify_callbacks(job)
            await asyncio.sleep(0.1)

            job.eval_loss = job.train_loss * 1.1 if job.train_loss else 0.5
            job.metrics = {
                "perplexity": 2 ** (job.eval_loss or 0.5),
                "accuracy": 0.85,
            }

            # Complete
            job.status = TrainingStatus.COMPLETED
            job.completed_at = datetime.now()
            job.output_path = job.config.output_dir

            Path(job.config.output_dir).mkdir(parents=True, exist_ok=True)

            logger.info(f"Job {job_id} completed successfully")

        except Exception as e:
            job.status = TrainingStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            logger.error(f"Job {job_id} failed: {e}")

        self._notify_callbacks(job)
        return job

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running job."""
        job = self._jobs.get(job_id)
        if not job:
            return False

        if job.status in (TrainingStatus.PENDING, TrainingStatus.PREPARING):
            job.status = TrainingStatus.CANCELLED
            job.completed_at = datetime.now()
            self._notify_callbacks(job)
            return True

        return False

    def get_latest_model(self) -> Optional[Path]:
        """Get the path to the most recently completed model."""
        completed = [
            j for j in self._jobs.values()
            if j.status == TrainingStatus.COMPLETED and j.output_path
        ]

        if not completed:
            return None

        latest = max(completed, key=lambda j: j.completed_at or datetime.min)
        return Path(latest.output_path) if latest.output_path else None


# Global instances
_collector: Optional[DatasetCollector] = None
_pipeline: Optional[FineTuningPipeline] = None
_global_lock = threading.Lock()


def get_data_collector(storage_path: Optional[Path] = None) -> DatasetCollector:
    """Get or create the global data collector."""
    global _collector
    with _global_lock:
        if _collector is None:
            _collector = DatasetCollector(storage_path)
        return _collector


def get_fine_tuning_pipeline(output_dir: Optional[Path] = None) -> FineTuningPipeline:
    """Get or create the global fine-tuning pipeline."""
    global _pipeline
    with _global_lock:
        if _pipeline is None:
            collector = get_data_collector()
            _pipeline = FineTuningPipeline(collector, output_dir)
        return _pipeline


def reset_fine_tuning() -> None:
    """Reset global instances (for testing)."""
    global _collector, _pipeline
    with _global_lock:
        _collector = None
        _pipeline = None
