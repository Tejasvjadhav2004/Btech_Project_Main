# Quick Start Guide

Get the Supply Chain Management System running in 5 minutes!

## 🚀 Setup in 5 Steps

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Start MongoDB

```bash
docker-compose up -d
```

Wait a few seconds for MongoDB to start. Verify it's running:
```bash
docker-compose ps
```

### Step 3: Place Your Data Files

Put your CSV files in the `data/` directory:
- `supply_chain_data.csv`
- `fashion_boutique_dataset.csv`

### Step 4: Seed the Database

```bash
python scripts/seed_data.py
```

This will load and transform your data into MongoDB.

### Step 5: Start the Applications

**Terminal 1 - Start FastAPI Backend:**
```bash
uvicorn api.main:app --reload
```

**Terminal 2 - Start Streamlit Dashboard:**
```bash
streamlit run dashboard/app.py
```

## 🎉 Access Your System

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501
- **MongoDB Express**: http://localhost:8081 (admin/admin123)

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

### MongoDB won't start

```bash
# Check logs
docker-compose logs mongodb

# Restart MongoDB
docker-compose restart mongodb

# Stop and remove volumes (fresh start)
docker-compose down -v
docker-compose up -d
```

### Can't connect to MongoDB

1. Check if MongoDB is running: `docker-compose ps`
2. Check your `.env` file has correct `MONGODB_URI`
3. Wait a few seconds for MongoDB to fully start

### Dashboard shows no data

1. Make sure you ran the seed script: `python scripts/seed_data.py`
2. Check the seed script output for errors
3. Verify data in MongoDB Express at http://localhost:8081

### API returns errors

1. Check the terminal where uvicorn is running for error messages
2. Verify all dependencies are installed: `pip list`
3. Check your `.env` file is configured correctly

## 📝 Next Steps

1. **Explore the dashboard** - Navigate through all pages
2. **Test the APIs** - Try all endpoints in `/docs`
3. **Create orders** - Simulate order processing
4. **Monitor alerts** - Watch for low stock warnings
5. **Check MongoDB** - View your data in MongoDB Express

## 🎓 Learn More

- Read the [README.md](README.md) for detailed documentation
- Check the [Architect Plan](plans/phase1_architect_plan.md) for system design
- See [EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md) for sample data and responses

## 🐛 Getting Help

If you encounter issues:

1. Check the terminal logs
2. Review MongoDB logs: `docker-compose logs mongodb`
3. Verify all files are in correct locations
4. Ensure dependencies are installed

## 🚀 Ready for Production?

To prepare for production:

1. Update `.env` with production settings
2. Use environment variables for sensitive data
3. Set up proper MongoDB authentication
4. Configure CORS for your domain
5. Add logging and monitoring
6. Set up backups for MongoDB

---

**You're ready to go! 🎉**
