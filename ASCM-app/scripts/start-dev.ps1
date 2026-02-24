# Start dev environment: create venv, install, run quick train, and launch Streamlit
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r frontend/requirements.txt
pip install -r ml/requirements.txt
python sample_data/generate_sample_data.py
python ml/train.py --train-quick
streamlit run frontend/app.py
