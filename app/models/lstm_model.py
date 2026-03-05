"""
LSTM Reliability Predictor
----------------------------
Uses a 2-layer LSTM to predict a supplier's future reliability score (0-100)
from their past purchase order sequence.

Input features per order:
  [0] OTD   — 1.0 if on-time, 0.0 if late
  [1] Qual  — quality_rating / 5.0
  [2] Price — unit_price / 200.0  (normalised)

Output: predicted reliability score in [0, 100]
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Optional, List


# ── Neural Network Architecture ──────────────────────────────────────────────

class SupplierLSTM(nn.Module):
    """
    2-layer stacked LSTM with dropout + a fully-connected head.
    Sigmoid activation ensures output is in [0, 1].
    """

    def __init__(
        self,
        input_size: int = 3,
        hidden_size: int = 32,
        num_layers: int = 2,
        output_size: int = 1,
        dropout: float = 0.2,
    ):
        super(SupplierLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size,
            hidden_size,
            num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.fc = nn.Linear(hidden_size, output_size)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])      # take last time-step
        return self.sigmoid(out)


# ── Predictor Wrapper ─────────────────────────────────────────────────────────

class LSTMReliabilityPredictor:
    """
    Per-supplier LSTM predictor.

    Usage:
        predictor = LSTMReliabilityPredictor()
        score = predictor.predict_reliability(supplier.orders)
        # Returns float in [0, 100] or None if not enough history
    """

    SEQ_LEN = 4        # number of past orders used as one input window
    EPOCHS  = 200      # training epochs (fast on small data)
    LR      = 0.01

    def __init__(self):
        self.model   = SupplierLSTM()
        self.trained = False

    # ── Feature extraction ────────────────────────────────────────────────────

    def _extract_features(self, orders) -> List[List[float]]:
        """Convert order ORM objects → list of [otd, quality_norm, price_norm]."""
        features = []
        for o in orders:
            if o.actual_delivery and o.expected_delivery:
                otd = 1.0 if (o.actual_delivery - o.expected_delivery).days <= 3 else 0.0
            else:
                otd = 0.5

            quality = (o.quality_rating / 5.0) if o.quality_rating else 0.8
            price   = min(1.0, (o.unit_price or 120.0) / 200.0)
            features.append([otd, quality, price])
        return features

    # ── Training ──────────────────────────────────────────────────────────────

    def train_on_orders(self, orders) -> bool:
        """
        Train the LSTM on a supplier's full order history.
        Returns True on success, False if there is not enough data.
        """
        features = self._extract_features(orders)
        if len(features) < self.SEQ_LEN + 1:
            return False

        X_list, y_list = [], []
        for i in range(len(features) - self.SEQ_LEN):
            X_list.append(features[i : i + self.SEQ_LEN])
            nxt = features[i + self.SEQ_LEN]
            # Target: weighted combination of OTD and quality for next period
            y_list.append(nxt[0] * 0.6 + nxt[1] * 0.4)

        X = torch.tensor(X_list, dtype=torch.float32)
        y = torch.tensor(y_list, dtype=torch.float32).unsqueeze(1)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.LR)
        loss_fn   = nn.MSELoss()

        self.model.train()
        for _ in range(self.EPOCHS):
            optimizer.zero_grad()
            pred = self.model(X)
            loss = loss_fn(pred, y)
            loss.backward()
            optimizer.step()

        self.trained = True
        return True

    # ── Inference ─────────────────────────────────────────────────────────────

    def predict_reliability(self, orders) -> Optional[float]:
        """
        Predict the supplier's next-period reliability score (0–100).
        Returns None if history is too short to train.
        """
        if not self.trained:
            if not self.train_on_orders(orders):
                return None

        features = self._extract_features(orders)
        if len(features) < self.SEQ_LEN:
            return None

        last_seq  = torch.tensor(
            [features[-self.SEQ_LEN :]], dtype=torch.float32
        )
        self.model.eval()
        with torch.no_grad():
            pred = self.model(last_seq).item()     # value in [0, 1]

        return round(pred * 100, 1)                # scale to [0, 100]
