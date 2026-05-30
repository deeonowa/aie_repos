# Самопроверка проекта

| # | Критерий | Статус | Где реализовано |
|---|----------|--------|-----------------|
| 1 | Сервис запускается по инструкциям из `project/README.md` | ✅ | `README.md`, разделы «Требования и установка», «Как запустить»|
| 2 | `/predict` использует обученную модель | ✅ | `src/service/api.py`, `src/models/predict.py`, `artifacts/cve_model.joblib` |
| 3 | EDA и эксперимент с метриками | ✅ | `notebooks/01_eda.ipynb`, `notebooks/02_experiments.ipynb`, `artifacts/metrics_all.json` |
| 4 | Сравнение моделей по метрикам | ✅ | `artifacts/metrics_all.json`, `artifacts/best_model.json`, `artifacts/figures/` |
| 5 | Структура модулей в `src/` | ✅ | `src/data/`, `src/features/`, `src/models/`, `src/service/`, `src/utils/`, `src/train.py` |
| 6 | Сценарий развёртывания в README | ✅ | `Dockerfile`, `docker-compose.yml`; `README.md`, раздел «Как запустить» |
| 7 | `.env.example`, секреты не в репозитории | ✅ | `configs/.env.example`, `.gitignore` (игнорирует .env); `report.md`, раздел «Наблюдаемость, конфигурация и безопасность» |
| 8 | Логи и `/health` | ✅ | `src/service/api.py` (logging, GET /health); `report.md`, раздел «Наблюдаемость, конфигурация и безопасность», подраздел «Логи и наблюдаемость» |
| 9 | Обоснование финальной модели | ✅ | `report.md`, раздел «Экспериментальный протокол и результаты», подраздел «Выбор финальной модели» |
| 10 | Сценарий демонстрации | ✅ | `README.md`, раздел «Демонстрация на защите»; `report.md`, раздел «Сценарий демонстрации на защите». |

**Самооценка:** 10 / 10.
