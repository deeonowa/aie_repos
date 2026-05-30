from src.data.load_nvd import build_dataset

if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    build_dataset()
