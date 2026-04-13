# Quick Start Guide

Get the Supply Chain Management System running in 4 minutes!

## 🚀 Setup in 4 Steps

### Step 1: Configure MongoDB Atlas

Copy `backend/.env.example` to `backend/.env` and configure your MongoDB Atlas connection:
```bash
cp backend/.env.example backend/.env
```

Update the `.env` file with your MongoDB Atlas connection string:
```env
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/
MONGODB_DATABASE_NAME=supply_chain_db
```

Replace `<username>`, `<password>`, and `<cluster>` with your MongoDB Atlas credentials.

### Step 2: Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### Step 3: Place Your Data Files

Put your CSV files in the `data/` directory:
- `supply_chain_data.csv`
- `fashion_boutique_dataset.csv`

### Step 4: Seed the Database

```bash
python backend/scripts/seed_data.py
```

This will load and transform your data into MongoDB.

### Step 5: Start the Applications

**Terminal 1 - Start FastAPI Backend:**
```bash
uvicorn backend.api.main:app --reload
```

**Terminal 2 - Start Streamlit Dashboard:**
```bash
streamlit run backend/dashboard/app.py
```

## 🎉 Access Your System

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501

## 📊 What You'll See

### Dashboard Pages

1. **Overview**: System KPIs, stock distribution charts
2. **Warehouses**: Inventory by warehouse, utilization rates
3. **Stores**: Inventory by store, stock levels
4. **Products**: Product catalog with filters
5. **Alerts**: Low stock warnings and system alerts

### API Endpoints

Try these endpoints in your browser or with curl:

```bash
# Health check
curl http://localhost:8000/health

# Get all products
curl http://localhost:8000/api/products

# Get dashboard overview
curl http://localhost:8000/api/dashboard/overview

# Get low stock alerts
curl http://localhost:8000/api/dashboard/low-stock?threshold=20
```

## 🧪 Test Order Creation

Create a test order with curl:

```bash
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "ST001",
    "items": [
      {"sku": "SKU-001", "quantity": 5}
    ]
  }'
```

## 🔍 Troubleshooting

### Can't connect to MongoDB

1. Verify your MongoDB Atlas cluster is running
2. Check your `.env` file has correct `MONGODB_URI` connection string
3. Ensure your IP address is whitelisted in MongoDB Atlas
4. Verify your MongoDB Atlas credentials are correct

### Dashboard shows no data

1. Make sure you ran the seed script: `python scripts/seed_data.py`
2. Check the seed script output for errors
3. Verify data in your MongoDB Atlas dashboard

### API returns errors

1. Check the terminal where uvicorn is running for error messages
2. Verify all dependencies are installed: `pip list`
3. Check your `.env` file is configured correctly

## 📝 Next Steps

1. **Explore the dashboard** - Navigate through all pages
2. **Test the APIs** - Try all endpoints in `/docs`
3. **Create orders** - Simulate order processing
4. **Monitor alerts** - Watch for low stock warnings
5. **Check MongoDB** - View your data in MongoDB Atlas dashboard

## 🎓 Learn More

- Read the [README.md](README.md) for detailed documentation
- Check the [Architect Plan](plans/phase1_architect_plan.md) for system design
- See [EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md) for sample data and responses

## 🐛 Getting Help

If you encounter issues:

1. Check the terminal logs
2. Review your MongoDB Atlas dashboard for connection issues
3. Verify all files are in correct locations
4. Ensure dependencies are installed

## 🚀 Ready for Production?

To prepare for production:

1. Update `.env` with production settings
2. Use environment variables for sensitive data
3. Use production-ready MongoDB Atlas cluster
4. Configure CORS for your domain
5. Add logging and monitoring
6. Ensure MongoDB Atlas backups are configured

---

**You're ready to go! 🎉**
