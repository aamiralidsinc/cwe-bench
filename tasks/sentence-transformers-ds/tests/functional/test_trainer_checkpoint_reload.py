from __future__ import annotations

from pathlib import Path

import torch
from tokenizers import Tokenizer
from tokenizers.models import WordLevel

from datasets import Dataset
from sentence_transformers import (
    SentenceTransformer,
    SentenceTransformerTrainer,
    SentenceTransformerTrainingArguments,
)
from sentence_transformers.base.modules import Module
from sentence_transformers.sentence_transformer.losses import MultipleNegativesRankingLoss
from sentence_transformers.sentence_transformer.modules import StaticEmbedding


class ProgrammaticModule(Module):
    """A module class that only exists in the program that builds the model."""

    def __init__(self, factor: float = 2.0):
        super().__init__()
        self.factor = factor

    def forward(self, features: dict, **kwargs):
        return features

    def get_config_dict(self):
        return {"factor": self.factor}

    def save(self, output_path: str, *args, **kwargs) -> None:
        self.save_config(output_path)


def _model() -> SentenceTransformer:
    tokenizer = Tokenizer(WordLevel({"[UNK]": 0, "alpha": 1, "beta": 2, "gamma": 3}, unk_token="[UNK]"))
    static = StaticEmbedding(tokenizer, embedding_dim=8)
    return SentenceTransformer(modules=[static, ProgrammaticModule()])


def test_training_restores_its_own_checkpoint(tmp_path: Path) -> None:
    """A training run restores the checkpoint it saved itself, even though the model was built
    programmatically with a module class that is not part of the library."""
    model = _model()
    dataset = Dataset.from_dict(
        {
            "anchor": ["alpha", "beta", "gamma", "alpha"],
            "positive": ["beta", "gamma", "alpha", "beta"],
        }
    )
    output_dir = tmp_path / "out"
    args = SentenceTransformerTrainingArguments(
        output_dir=str(output_dir),
        max_steps=2,
        per_device_train_batch_size=2,
        save_strategy="steps",
        save_steps=1,
        logging_steps=1,
        report_to=[],
        use_cpu=True,
        seed=0,
        dataloader_num_workers=0,
    )
    trainer = SentenceTransformerTrainer(
        model=model,
        args=args,
        train_dataset=dataset,
        loss=MultipleNegativesRankingLoss(model),
    )
    trainer.train()

    checkpoints = sorted(output_dir.glob("checkpoint-*"))
    assert checkpoints, "training saved no checkpoint"

    trainer.train(resume_from_checkpoint=str(checkpoints[-1]))

    assert type(model[-1]).__name__ == "ProgrammaticModule"
    assert model[-1].factor == 2.0
    embeddings = model.encode(["alpha beta"], convert_to_tensor=True)
    assert torch.isfinite(embeddings).all()
