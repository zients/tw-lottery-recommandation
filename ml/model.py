# ml/model.py
import torch
import torch.nn as nn


class LotteryTransformer(nn.Module):
    """Transformer that predicts next-draw number probabilities.

    Input:  (batch, context_len, num_count) multi-hot float
    Output: (batch, num_count) logits — apply sigmoid for probabilities
    """

    def __init__(
        self,
        num_count: int,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dropout: float = 0.1,
        max_context: int = 512,
    ):
        super().__init__()
        self.input_proj = nn.Linear(num_count, d_model)
        self.pos_embedding = nn.Embedding(max_context, d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.output = nn.Linear(d_model, num_count)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, num_count)
        batch, seq_len, _ = x.shape
        positions = torch.arange(seq_len, device=x.device).unsqueeze(0).expand(batch, -1)
        h = self.input_proj(x) + self.pos_embedding(positions)
        h = self.transformer(h)
        return self.output(h[:, -1, :])  # take last timestep
