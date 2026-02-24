import pandas as pd
import numpy as np
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'synthetic_orders.csv'

n = 50
np.random.seed(0)
ids = range(1, n+1)
lat = 37.7 + np.random.rand(n)*0.1
lon = -122.4 + np.random.rand(n)*0.1
demand = np.random.poisson(20, n)

df = pd.DataFrame({
    'order_id': ids,
    'lat': lat,
    'lon': lon,
    'quantity': demand,
})

df.to_csv(OUT, index=False)
print(f'Wrote sample data to {OUT}')
