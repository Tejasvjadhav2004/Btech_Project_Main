# SCM Frontend

This is replacing the legacy Streamlit frontend with a simple, clean React Application using plain JavaScript and inline CSS.

## Features
- **Dashboard**: High-level overview, KPIs, recent activity.
- **Inventory**: Browse products, view stock levels.
- **Forecast**: Simple demand forecast visualizations.
- **Alerts**: Auto-refreshing alerts from the intelligence layer.
- **Orders**: Create new orders and view order history.
- **Logs**: View execution logs and anomalies.

## Tech Stack
- React 18
- Vite
- Axios
- Inline CSS (No Tailwind)

## Setup instructions

1. Run `npm install` inside the `frontend` directory.
2. Edit `.env` to ensure `VITE_API_BASE_URL` points to your running FastAPI backend (defaults to `http://localhost:8000`).
3. Run `npm run dev` to start the development server.

## No Extra Dependencies
This project uses plain JavaScript and `useState/useEffect` hooks without Redux or Tailwind, ensuring maximum simplicity as per requirements.
