# ML Service (ml)

This folder contains a minimal Graph Neural Network (GNN) stub and a tiny forecasting demo used by the Streamlit frontend.

Notes:

- `gnn_model.py` will try to import PyTorch Geometric (PyG). If PyG is not available, the code falls back to a NetworkX-based heuristic so the demo remains runnable.
- To install PyG, follow the official instructions at https://pytorch-geometric.readthedocs.io/ (installation is platform-dependent).

Files:

- `gnn_model.py` — GNN stub with `RouteGNN.predict(graph)` interface.
- `train.py` — small demo forecasting script used by the Streamlit app.

Run quick demo:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python train.py --train-quick
```
