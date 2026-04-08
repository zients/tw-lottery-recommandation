# ml/train.py
from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ml.dataset import LotteryDataset, is_oos_split
from ml.model import LotteryTransformer


CHECKPOINT_DIR = Path("ml/checkpoints")


def coverage(logits: torch.Tensor, targets: torch.Tensor, pick: int) -> float:
    """Average fraction of actual drawn numbers that appear in top-pick predictions."""
    probs = torch.sigmoid(logits)
    topk = probs.topk(pick, dim=1).indices  # (batch, pick)
    total = 0.0
    for i in range(targets.size(0)):
        actual = targets[i].nonzero(as_tuple=True)[0].tolist()
        predicted = set(topk[i].tolist())
        total += len([n for n in actual if n in predicted]) / max(len(actual), 1)
    return total / targets.size(0)


def train(
    draws: list[tuple[str, list[int]]],
    lottery_type: str,
    num_range: tuple[int, int],
    analyze_count: int,
    pick: int,
    context_len: int = 30,
    epochs: int = 100,
    batch_size: int = 64,
    lr: float = 1e-3,
) -> Path:
    is_draws, oos_draws = is_oos_split(draws)
    if len(is_draws) < context_len + 1:
        raise ValueError(f"Not enough IS data: {len(is_draws)} draws (need >{context_len})")

    ds_train = LotteryDataset(is_draws, context_len, num_range, analyze_count)
    ds_oos = LotteryDataset(
        is_draws[-context_len:] + oos_draws,
        context_len, num_range, analyze_count,
    )

    dl_train = DataLoader(ds_train, batch_size=batch_size, shuffle=True)
    dl_oos = DataLoader(ds_oos, batch_size=batch_size)

    num_count = num_range[1] - num_range[0] + 1
    model = LotteryTransformer(num_count)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCEWithLogitsLoss()

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    best_path = CHECKPOINT_DIR / f"{lottery_type}_best.pt"
    best_cov = -1.0

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for ctx, tgt in dl_train:
            optimizer.zero_grad()
            logits = model(ctx)
            loss = criterion(logits, tgt)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        if len(dl_oos.dataset) > 0 and epoch % 10 == 0:
            model.eval()
            with torch.no_grad():
                all_logits, all_targets = [], []
                for ctx, tgt in dl_oos:
                    all_logits.append(model(ctx))
                    all_targets.append(tgt)
                cov = coverage(
                    torch.cat(all_logits), torch.cat(all_targets), pick
                )
            model.train()
            print(f"Epoch {epoch:3d} | loss {train_loss/len(dl_train):.4f} | OOS coverage {cov:.3f}")
            if cov > best_cov:
                best_cov = cov
                torch.save(model.state_dict(), best_path)
        elif epoch % 10 == 0:
            print(f"Epoch {epoch:3d} | loss {train_loss/len(dl_train):.4f}")

    if not best_path.exists():
        torch.save(model.state_dict(), best_path)

    print(f"\nBest OOS coverage: {best_cov:.3f} → saved to {best_path}")
    return best_path
