import pandas as pd
import numpy as np
import argparse
from pathlib import Path

SAMPLE = Path(__file__).resolve(
).parents[1] / 'sample_data' / 'synthetic_orders.csv'


def quick_forecast():
    """Produce a tiny synthetic forecast DataFrame for demo plotting."""
    # create a simple time series
    idx = pd.date_range(end=pd.Timestamp.today(), periods=30)
    y = np.linspace(100, 150, len(idx)) + np.random.normal(0, 2, len(idx))
    df = pd.DataFrame({'ds': idx, 'y': y})
    # very simple 'prediction' future
    future_idx = pd.date_range(
        start=idx[-1] + pd.Timedelta(days=1), periods=14)
    yhat = np.linspace(y[-1], y[-1] + 10, len(future_idx))
    df_forecast = pd.DataFrame({'ds': future_idx, 'yhat': yhat})
    return df_forecast


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--train-quick', action='store_true')
    args = parser.parse_args()

    if args.train_quick:
        print('Running quick forecast demo...')
        df_forecast = quick_forecast()
        print(df_forecast.head())
    else:
        print('No heavy training included in scaffold. Use --train-quick for demo.')
