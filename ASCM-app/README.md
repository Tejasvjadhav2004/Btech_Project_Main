# ASCM-app

AI Supply Chain Management (ASCM) demo application.

This scaffold contains a minimal, runnable example that demonstrates:

- Streamlit dashboard frontend
- ML service with a Graph Neural Network (GNN) stub and forecasting utilities
- LangChain orchestration adapter stub for decision-support
- Supabase/Postgres integration placeholders
- Docker Compose for local development

Quick start (Windows PowerShell):

```powershell
# create & activate venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# install dependencies
pip install -r frontend/requirements.txt
pip install -r ml/requirements.txt

# generate sample data and run a quick training pass
python sample_data/generate_sample_data.py
python ml/train.py --train-quick

# run Streamlit app
streamlit run frontend/app.py
```

Run with Docker Compose:

```powershell
docker-compose -f infra/docker-compose.yml up --build
```

Notes:

- This scaffold includes a PyTorch Geometric (PyG) stub. Installing PyG may require additional system steps; see `ml/README.md` for instructions. The GNN file falls back to a NetworkX-based stub if PyG is not available so you can run the demo without GPU.
- For production, connect a real Supabase project and set the environment variables from `infra/.env.example`.

Next steps:

- Replace synthetic data with your dataset
- Implement full GNN architecture with PyG or DGL
- Add authentication, logging, and robust error handling

License: MIT
