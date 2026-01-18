# HW06 – Report

> Файл: `homeworks/HW06/report.md`  

## 1. Dataset

- Какой датасет выбран: S06-hw-dataset-02.csv
- Размер: 18000 строк, 39 столбцов
- Целевая переменная: `target` (Бинарные значения, доли 0: 13273, 1: 4727)
- Признаки: числовые

## 2. Protocol

- Разбиение: train/test (13500/4500), `random_state`: 42
- Подбор: CV на train (5 фолдов, оптимизирует кацество модели несбалансированного набора данных)
- Метрики: accuracy, F1, ROC-AUC (Так как целевая содержит бинарные значения)

## 3. Models

- DummyClassifier (baseline)
- LogisticRegression (baseline из S05)
- DecisionTreeClassifier (контроль сложности: `max_depth` + `min_samples_leaf` или `ccp_alpha`)
- RandomForestClassifier  (подбор `max_depth` и `min_samples_leaf`, `max_features` задан как квадратный корень)
- HistGradientBoosting (подбор `learning_rate`, `max_depth`, `max_leaf_nodes`)
- StackingClassifier (Использованы LogisticRegression, DecisionTreeClassifier, RandomForestClassifier модели и HistGradientBoosting как метамодель)

## 4. Results

|Модель|accuracy|f1|roc_auc|
|:-|:-|:-|:-|
|Stacking|0.9151|0.8313|0.9342|
|HistGradientBoosting|0.9084|0.8103|0.9318|
|RandomForest|0.8922|0.7593|0.9301|
|DecisionTree|0.8296|0.6486|0.8419|
|LogReg(scaled)|0.8162|0.5717|0.8009|
|Dummy|0.7373|0|0.5|

- По ROC-AUC лучшей моделью оказалась Stacking, так как объединяет в себе правильно подобранные другие модели, использованные ранее, и правильную метамодель 

## 5. Analysis

- Устойчивость: если поменять `random_state` (хотя бы 5 прогонов для 1-2 моделей) нарушится стабильность результатов (они будут отлечаться)
- Ошибки: Confusion matrix для модели Stacking на тестовых данных показывает бинарную классификацию с классами 0 и 1. Модель демонстрирует хорошую производительность, но с заметными ошибками в предсказаниях положительного класса.
- Интерпретация: Самые влиятельные на обучения метрики это f16, f01, f07, f19 и f30

## 6. Conclusion

В рамках проделанном мною работы я пришел к выводам, что ансамбли хорошо подходят для обучаения модели с бинарными данными. В рамках честного ML-эксперимента важно точно подобрать гиперпараметры. Честный ML-эксперимент требует baseline, train/test split, фиксацию random_state и кросс-валидацию для воспроизводимости. 5+ прогонов с разными random_state выявляют разброс показателей.
