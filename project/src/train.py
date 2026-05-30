"""Точка входа: python -m src.train"""

import logging

from src.models.train import train_and_save

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    summary = train_and_save()
    print("Training finished.")
    print(f"Model: {summary['model_name']}")
    print(f"Test metrics: {summary['test_metrics']}")
