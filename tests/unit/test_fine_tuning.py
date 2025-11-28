"""Tests for the fine-tuning pipeline."""

import pytest
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

from src.core.fine_tuning import (
    DatasetCollector,
    DatasetFormat,
    FineTuningPipeline,
    TrainingConfig,
    TrainingJob,
    TrainingSample,
    TrainingStatus,
    get_data_collector,
    get_fine_tuning_pipeline,
    reset_fine_tuning,
)


class TestTrainingSample:
    """Tests for TrainingSample class."""

    def test_create_sample(self):
        """Test creating a training sample."""
        sample = TrainingSample(
            sample_id="s_1",
            instruction="Summarize the company",
            output="The company is a tech firm...",
        )
        assert sample.sample_id == "s_1"
        assert sample.instruction == "Summarize the company"
        assert sample.source == "agent"

    def test_to_alpaca(self):
        """Test Alpaca format conversion."""
        sample = TrainingSample(
            sample_id="s_1",
            instruction="Analyze revenue",
            input="Revenue data: $10M",
            output="Revenue is $10M",
            system="You are a financial analyst",
        )
        data = sample.to_alpaca()

        assert data["instruction"] == "Analyze revenue"
        assert data["input"] == "Revenue data: $10M"
        assert data["output"] == "Revenue is $10M"
        assert data["system"] == "You are a financial analyst"

    def test_to_sharegpt(self):
        """Test ShareGPT format conversion."""
        sample = TrainingSample(
            sample_id="s_1",
            instruction="What is AI?",
            output="AI is artificial intelligence.",
            system="Be helpful",
        )
        data = sample.to_sharegpt()

        assert "conversations" in data
        assert len(data["conversations"]) == 3  # system, human, gpt
        assert data["conversations"][0]["from"] == "system"
        assert data["conversations"][1]["from"] == "human"
        assert data["conversations"][2]["from"] == "gpt"

    def test_to_openai(self):
        """Test OpenAI messages format conversion."""
        sample = TrainingSample(
            sample_id="s_1",
            instruction="Explain ML",
            output="ML is machine learning.",
        )
        data = sample.to_openai()

        assert "messages" in data
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"

    def test_to_dict(self):
        """Test serialization."""
        sample = TrainingSample(
            sample_id="s_1",
            instruction="Test",
            output="Response",
            task_type="research",
            quality_score=0.9,
        )
        data = sample.to_dict()

        assert data["sample_id"] == "s_1"
        assert data["task_type"] == "research"
        assert data["quality_score"] == 0.9

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "sample_id": "s_2",
            "instruction": "Question",
            "output": "Answer",
            "source": "manual",
            "task_type": "qa",
        }
        sample = TrainingSample.from_dict(data)

        assert sample.sample_id == "s_2"
        assert sample.source == "manual"
        assert sample.task_type == "qa"


class TestTrainingConfig:
    """Tests for TrainingConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = TrainingConfig()

        assert config.use_lora is True
        assert config.num_epochs == 3
        assert config.batch_size == 4
        assert config.learning_rate == 2e-4

    def test_custom_config(self):
        """Test custom configuration."""
        config = TrainingConfig(
            base_model="custom/model",
            num_epochs=5,
            lora_r=32,
        )

        assert config.base_model == "custom/model"
        assert config.num_epochs == 5
        assert config.lora_r == 32

    def test_to_dict(self):
        """Test serialization."""
        config = TrainingConfig(num_epochs=10)
        data = config.to_dict()

        assert data["num_epochs"] == 10
        assert "lora_r" in data
        assert "target_modules" in data

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "base_model": "test/model",
            "num_epochs": 7,
            "batch_size": 8,
        }
        config = TrainingConfig.from_dict(data)

        assert config.base_model == "test/model"
        assert config.num_epochs == 7
        assert config.batch_size == 8


class TestTrainingJob:
    """Tests for TrainingJob class."""

    def test_create_job(self):
        """Test creating a training job."""
        config = TrainingConfig()
        job = TrainingJob(
            job_id="job_1",
            config=config,
            dataset_path="/data/train.json",
        )

        assert job.job_id == "job_1"
        assert job.status == TrainingStatus.PENDING
        assert job.progress == 0.0

    def test_progress_calculation(self):
        """Test progress calculation."""
        config = TrainingConfig()
        job = TrainingJob(
            job_id="job_1",
            config=config,
            dataset_path="/data/train.json",
            total_steps=100,
            current_step=50,
        )

        assert job.progress == 0.5

    def test_progress_empty(self):
        """Test progress with no steps."""
        config = TrainingConfig()
        job = TrainingJob(
            job_id="job_1",
            config=config,
            dataset_path="/data/train.json",
        )

        assert job.progress == 0.0

    def test_to_dict(self):
        """Test serialization."""
        config = TrainingConfig()
        job = TrainingJob(
            job_id="job_1",
            config=config,
            dataset_path="/data/train.json",
            train_loss=0.5,
        )
        data = job.to_dict()

        assert data["job_id"] == "job_1"
        assert data["status"] == "pending"
        assert data["train_loss"] == 0.5


class TestDatasetCollector:
    """Tests for DatasetCollector class."""

    def setup_method(self):
        """Create temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.collector = DatasetCollector(Path(self.temp_dir))

    def teardown_method(self):
        """Cleanup temp directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_sample(self):
        """Test adding a sample."""
        sample = self.collector.add_sample(
            instruction="What is Python?",
            output="Python is a programming language.",
        )

        assert sample.sample_id
        assert sample.instruction == "What is Python?"
        assert self.collector.count == 1

    def test_add_sample_with_metadata(self):
        """Test adding sample with metadata."""
        sample = self.collector.add_sample(
            instruction="Test",
            output="Response",
            task_type="qa",
            quality_score=0.95,
            metadata={"model": "gpt-4"},
        )

        assert sample.task_type == "qa"
        assert sample.quality_score == 0.95
        assert sample.metadata["model"] == "gpt-4"

    def test_add_conversation(self):
        """Test adding samples from conversation."""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm doing well!"},
        ]

        samples = self.collector.add_conversation(messages)

        assert len(samples) == 2
        assert samples[0].system == "You are helpful"

    def test_get_sample(self):
        """Test getting a sample."""
        added = self.collector.add_sample(
            instruction="Test",
            output="Response",
        )

        retrieved = self.collector.get_sample(added.sample_id)
        assert retrieved is not None
        assert retrieved.instruction == "Test"

    def test_list_samples(self):
        """Test listing samples."""
        for i in range(5):
            self.collector.add_sample(
                instruction=f"Q{i}",
                output=f"A{i}",
            )

        samples = self.collector.list_samples()
        assert len(samples) == 5

    def test_list_samples_by_task_type(self):
        """Test filtering by task type."""
        self.collector.add_sample(
            instruction="Q1", output="A1", task_type="research"
        )
        self.collector.add_sample(
            instruction="Q2", output="A2", task_type="qa"
        )

        research = self.collector.list_samples(task_type="research")
        assert len(research) == 1

    def test_list_samples_by_quality(self):
        """Test filtering by quality."""
        self.collector.add_sample(
            instruction="Q1", output="A1", quality_score=0.9
        )
        self.collector.add_sample(
            instruction="Q2", output="A2", quality_score=0.5
        )

        high_quality = self.collector.list_samples(min_quality=0.7)
        assert len(high_quality) == 1

    def test_remove_sample(self):
        """Test removing a sample."""
        sample = self.collector.add_sample(
            instruction="Test",
            output="Response",
        )

        success = self.collector.remove_sample(sample.sample_id)
        assert success
        assert self.collector.count == 0

    def test_update_quality(self):
        """Test updating quality score."""
        sample = self.collector.add_sample(
            instruction="Test",
            output="Response",
        )

        success = self.collector.update_quality(sample.sample_id, 0.85)
        assert success

        updated = self.collector.get_sample(sample.sample_id)
        assert updated.quality_score == 0.85

    def test_export_dataset_alpaca(self):
        """Test exporting in Alpaca format."""
        self.collector.add_sample(
            instruction="Q1",
            output="A1",
        )

        output_path = Path(self.temp_dir) / "export" / "data.json"
        count = self.collector.export_dataset(
            output_path,
            format=DatasetFormat.ALPACA,
        )

        assert count == 1
        assert output_path.exists()

    def test_export_dataset_sharegpt(self):
        """Test exporting in ShareGPT format."""
        self.collector.add_sample(
            instruction="Q1",
            output="A1",
        )

        output_path = Path(self.temp_dir) / "export" / "sharegpt.json"
        count = self.collector.export_dataset(
            output_path,
            format=DatasetFormat.SHAREGPT,
        )

        assert count == 1

    def test_get_statistics(self):
        """Test getting statistics."""
        self.collector.add_sample(
            instruction="Q1", output="A1",
            source="agent", task_type="research",
            quality_score=0.9,
        )
        self.collector.add_sample(
            instruction="Q2", output="A2",
            source="manual", task_type="qa",
            quality_score=0.8,
        )

        stats = self.collector.get_statistics()

        assert stats["total"] == 2
        assert stats["by_source"]["agent"] == 1
        assert stats["by_source"]["manual"] == 1
        assert stats["by_task_type"]["research"] == 1
        assert abs(stats["avg_quality"] - 0.85) < 0.01

    def test_persistence(self):
        """Test data persists across instances."""
        self.collector.add_sample(
            instruction="Persistent",
            output="Data",
        )

        # Create new collector with same path
        new_collector = DatasetCollector(Path(self.temp_dir))
        assert new_collector.count == 1


class TestFineTuningPipeline:
    """Tests for FineTuningPipeline class."""

    def setup_method(self):
        """Create temp directory."""
        reset_fine_tuning()
        self.temp_dir = tempfile.mkdtemp()
        self.collector = DatasetCollector(Path(self.temp_dir) / "data")
        self.pipeline = FineTuningPipeline(
            collector=self.collector,
            output_dir=Path(self.temp_dir) / "output",
        )

    def teardown_method(self):
        """Cleanup."""
        reset_fine_tuning()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_prepare_dataset(self):
        """Test dataset preparation."""
        # Add samples
        for i in range(10):
            self.collector.add_sample(
                instruction=f"Question {i}",
                output=f"Answer {i}",
            )

        paths = self.pipeline.prepare_dataset(
            output_name="test_dataset",
            train_split=0.8,
        )

        assert "train" in paths
        assert "eval" in paths
        assert paths["train"].exists()
        assert paths["eval"].exists()

    def test_prepare_dataset_empty(self):
        """Test error on empty dataset."""
        with pytest.raises(ValueError):
            self.pipeline.prepare_dataset(output_name="empty")

    def test_create_job(self):
        """Test creating a training job."""
        job = self.pipeline.create_job(
            dataset_path="/data/train.json",
        )

        assert job.job_id.startswith("job_")
        assert job.status == TrainingStatus.PENDING

    def test_create_job_with_config(self):
        """Test creating job with custom config."""
        config = TrainingConfig(num_epochs=5)

        job = self.pipeline.create_job(
            dataset_path="/data/train.json",
            config=config,
        )

        assert job.config.num_epochs == 5

    def test_get_job(self):
        """Test getting a job."""
        created = self.pipeline.create_job(
            dataset_path="/data/train.json",
        )

        retrieved = self.pipeline.get_job(created.job_id)
        assert retrieved is not None
        assert retrieved.job_id == created.job_id

    def test_list_jobs(self):
        """Test listing jobs."""
        for _ in range(3):
            self.pipeline.create_job(dataset_path="/data/train.json")

        jobs = self.pipeline.list_jobs()
        assert len(jobs) == 3

    def test_list_jobs_by_status(self):
        """Test filtering jobs by status."""
        job = self.pipeline.create_job(dataset_path="/data/train.json")

        pending = self.pipeline.list_jobs(status=TrainingStatus.PENDING)
        assert len(pending) == 1

        running = self.pipeline.list_jobs(status=TrainingStatus.TRAINING)
        assert len(running) == 0

    @pytest.mark.asyncio
    async def test_run_job(self):
        """Test running a training job."""
        config = TrainingConfig(num_epochs=1)
        job = self.pipeline.create_job(
            dataset_path="/data/train.json",
            config=config,
        )

        result = await self.pipeline.run_job(job.job_id)

        assert result.status == TrainingStatus.COMPLETED
        assert result.train_loss is not None
        assert result.output_path is not None

    @pytest.mark.asyncio
    async def test_run_job_not_found(self):
        """Test error when job not found."""
        with pytest.raises(ValueError):
            await self.pipeline.run_job("nonexistent")

    def test_cancel_job(self):
        """Test cancelling a job."""
        job = self.pipeline.create_job(
            dataset_path="/data/train.json",
        )

        success = self.pipeline.cancel_job(job.job_id)
        assert success

        cancelled = self.pipeline.get_job(job.job_id)
        assert cancelled.status == TrainingStatus.CANCELLED

    def test_callback(self):
        """Test status callbacks."""
        updates = []

        def on_update(job):
            updates.append(job.status)

        self.pipeline.add_callback(on_update)
        job = self.pipeline.create_job(dataset_path="/data/train.json")
        self.pipeline.cancel_job(job.job_id)

        assert TrainingStatus.CANCELLED in updates

    @pytest.mark.asyncio
    async def test_get_latest_model(self):
        """Test getting latest model path."""
        config = TrainingConfig(num_epochs=1)
        job = self.pipeline.create_job(
            dataset_path="/data/train.json",
            config=config,
        )
        await self.pipeline.run_job(job.job_id)

        latest = self.pipeline.get_latest_model()
        assert latest is not None


class TestGlobalFunctions:
    """Tests for global functions."""

    def setup_method(self):
        """Reset before each test."""
        reset_fine_tuning()

    def teardown_method(self):
        """Reset after each test."""
        reset_fine_tuning()

    def test_get_data_collector_singleton(self):
        """Test singleton behavior."""
        c1 = get_data_collector()
        c2 = get_data_collector()
        assert c1 is c2

    def test_get_fine_tuning_pipeline_singleton(self):
        """Test singleton behavior."""
        p1 = get_fine_tuning_pipeline()
        p2 = get_fine_tuning_pipeline()
        assert p1 is p2

    def test_reset_fine_tuning(self):
        """Test resetting singletons."""
        c1 = get_data_collector()
        p1 = get_fine_tuning_pipeline()

        reset_fine_tuning()

        c2 = get_data_collector()
        p2 = get_fine_tuning_pipeline()

        assert c1 is not c2
        assert p1 is not p2
