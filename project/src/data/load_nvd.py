
import gzip
import json
import logging
import lzma
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from src.data.severity import cvss_to_severity
from src.utils.config import load_config, resolve_path

logger = logging.getLogger(__name__)


def _extract_cvss_from_metrics_block(metrics: dict[str, Any]) -> float | None:
    for key in ("cvssMetricV31", "cvssMetricV30"):
        entries = metrics.get(key)
        if not entries:
            continue
        for entry in entries:
            if entry.get("type") == "Primary":
                score = entry.get("cvssData", {}).get("baseScore")
                if score is not None:
                    return float(score)
        score = entries[0].get("cvssData", {}).get("baseScore")
        if score is not None:
            return float(score)
    return None


def _extract_cvss_v3_legacy(item: dict[str, Any]) -> float | None:
    impact = item.get("impact") or {}
    base_v3 = impact.get("baseMetricV3")
    if base_v3 and "cvssV3" in base_v3:
        score = base_v3["cvssV3"].get("baseScore")
        if score is not None:
            return float(score)
    base_v31 = impact.get("baseMetricV31")
    if base_v31 and "cvssV3" in base_v31:
        score = base_v31["cvssV3"].get("baseScore")
        if score is not None:
            return float(score)
    return None


def _extract_description_legacy(item: dict[str, Any]) -> str:
    desc_data = item.get("cve", {}).get("description", {}).get("description_data", [])
    for entry in desc_data:
        if entry.get("lang") == "en":
            return str(entry.get("value", "")).strip()
    if desc_data:
        return str(desc_data[0].get("value", "")).strip()
    return ""


def _extract_description_nvd20(item: dict[str, Any]) -> str:
    for entry in item.get("descriptions", []):
        if entry.get("lang") == "en":
            return str(entry.get("value", "")).strip()
    descriptions = item.get("descriptions", [])
    if descriptions:
        return str(descriptions[0].get("value", "")).strip()
    return ""


def _parse_item(
    item: dict[str, Any],
    medium_min: float,
    high_min: float,
) -> dict[str, Any] | None:
    if "cve" in item:
        cve_id = item.get("cve", {}).get("CVE_data_meta", {}).get("ID")
        description = _extract_description_legacy(item)
        cvss = _extract_cvss_v3_legacy(item)
    else:
        cve_id = item.get("id")
        description = _extract_description_nvd20(item)
        cvss = _extract_cvss_from_metrics_block(item.get("metrics", {}))

    if not cve_id or not description or cvss is None:
        return None

    severity, severity_id = cvss_to_severity(cvss, medium_min=medium_min, high_min=high_min)
    return {
        "cve_id": cve_id,
        "description": description,
        "cvss_base_score": cvss,
        "severity": severity,
        "severity_id": severity_id,
    }


def parse_nvd_json(
    raw_path: Path,
    medium_min: float = 4.0,
    high_min: float = 7.0,
) -> pd.DataFrame:
    with raw_path.open(encoding="utf-8") as f:
        payload = json.load(f)

    items = payload.get("CVE_Items") or payload.get("cve_items") or []
    rows: list[dict[str, Any]] = []
    for item in items:
        parsed = _parse_item(item, medium_min=medium_min, high_min=high_min)
        if parsed:
            rows.append(parsed)

    df = pd.DataFrame(rows)
    logger.info("Parsed %s CVE with CVSS v3 and English description", len(df))
    return df


def _download_file(url: str, out_path: Path) -> None:
    headers = {
        "User-Agent": "AIE-Course-CVE-Triage/2.0 (educational)",
    }
    logger.info("Downloading: %s", url)
    response = requests.get(url, timeout=300, headers=headers)
    response.raise_for_status()
    out_path.write_bytes(response.content)
    logger.info("Saved %s bytes to %s", len(response.content), out_path)


def download_nvd_feed(year: int, raw_dir: str | Path | None = None) -> Path:
    cfg = load_config()
    data_cfg = cfg["data"]
    raw_dir = resolve_path(raw_dir or data_cfg["raw_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)

    xz_path = raw_dir / f"CVE-{year}.json.xz"
    gz_path = raw_dir / f"nvdcve-1.1-{year}.json.gz"
    if xz_path.exists():
        return xz_path
    if gz_path.exists():
        return gz_path

    urls = [str(data_cfg["nvd_url"]).format(year=year)]
    fallback = data_cfg.get("nvd_url_fallback")
    if fallback:
        urls.append(str(fallback).format(year=year))

    last_error: Exception | None = None
    for url in urls:
        try:
            if url.endswith(".xz"):
                _download_file(url, xz_path)
                return xz_path
            _download_file(url, gz_path)
            return gz_path
        except requests.RequestException as exc:
            logger.warning("Failed to download from %s: %s", url, exc)
            last_error = exc

    raise RuntimeError(f"Could not download NVD feed for {year}") from last_error


def _decompress_json(archive_path: Path) -> Path:
    json_path = archive_path.with_suffix("")
    if json_path.exists():
        return json_path

    if archive_path.suffix == ".xz":
        with lzma.open(archive_path, "rb") as f_in:
            json_path.write_bytes(f_in.read())
    elif archive_path.suffix == ".gz":
        with gzip.open(archive_path, "rb") as f_in:
            json_path.write_bytes(f_in.read())
    else:
        raise ValueError(f"Unsupported archive: {archive_path}")
    return json_path


def _severity_thresholds(data_cfg: dict[str, Any]) -> tuple[float, float]:
    thresholds = data_cfg.get("severity_thresholds") or {}
    medium_min = float(thresholds.get("medium_min", 4.0))
    high_min = float(thresholds.get("high_min", 7.0))
    return medium_min, high_min


def _dataset_years(data_cfg: dict[str, Any]) -> list[int]:
    years = data_cfg.get("nvd_years")
    if years:
        return [int(y) for y in years]
    if "nvd_year" in data_cfg:
        return [int(data_cfg["nvd_year"])]
    return [2024]


def build_dataset_for_year(year: int, medium_min: float, high_min: float) -> pd.DataFrame:
    gz_path = download_nvd_feed(year=year)
    json_path = _decompress_json(gz_path)
    df = parse_nvd_json(json_path, medium_min=medium_min, high_min=high_min)
    return df.assign(nvd_year=year)


def build_dataset(
    years: list[int] | None = None,
    processed_path: str | Path | None = None,
    sample_path: str | Path | None = None,
) -> pd.DataFrame:
    cfg = load_config()
    data_cfg = cfg["data"]
    medium_min, high_min = _severity_thresholds(data_cfg)
    min_len = int(data_cfg["min_text_len"])
    max_len = int(data_cfg["max_text_len"])
    year_list = years or _dataset_years(data_cfg)

    parts: list[pd.DataFrame] = []
    for year in year_list:
        logger.info("Building dataset for year %s", year)
        parts.append(build_dataset_for_year(year, medium_min, high_min))

    df = pd.concat(parts, ignore_index=True)
    df = df.sort_values(["cve_id", "nvd_year"]).drop_duplicates(
        subset=["cve_id"], keep="last"
    )
    df["description"] = df["description"].str.slice(0, max_len)
    df = df[df["description"].str.len() >= min_len].copy()
    df = df.reset_index(drop=True)

    processed = resolve_path(processed_path or data_cfg["processed_path"])
    processed.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(processed, index=False)
    logger.info(
        "Saved processed dataset: %s (%s rows, years %s)",
        processed,
        len(df),
        year_list,
    )

    sample_n = int(data_cfg["sample_size"])
    sample = resolve_path(sample_path or data_cfg["sample_path"])
    df.sample(n=min(sample_n, len(df)), random_state=cfg["model"]["random_state"]).to_csv(
        sample, index=False
    )
    logger.info("Saved sample: %s", sample)
    return df


def load_processed_dataset(path: str | Path | None = None) -> pd.DataFrame:
    cfg = load_config()
    csv_path = resolve_path(path or cfg["data"]["processed_path"])
    if not csv_path.exists():
        sample = resolve_path(cfg["data"]["sample_path"])
        if sample.exists():
            logger.warning("Full dataset missing, using sample: %s", sample)
            return pd.read_csv(sample)
        raise FileNotFoundError(
            f"Dataset not found at {csv_path}. Run: python -m src.data"
        )
    return pd.read_csv(csv_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    build_dataset()
