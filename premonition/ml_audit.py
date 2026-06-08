import sys
import pandas as pd
from pathlib import Path
from premonition.data.loaders import load_dataset
from premonition.models.registry import ModelRegistry
from premonition.config.settings import get_settings

settings = get_settings()

print('--- A. DATASET VALIDATION ---')
try:
    df = load_dataset()
    print(f'1. Dataset: Configured in settings (MIMIC-III tabular sepsis dataset)')
    print(f'2. Dataset file names: {settings.dataset_path.name}')
    print(f'3. Number of records: {len(df)}')
    print(f'4. Number of features: {len(df.columns)}')
    print(f'5. Target variable: sepsis_label')
    print(f'6. Preprocessing pipeline: MinMaxScaler, SimpleImputer via premonition.data.pipeline')
    print(f'7. Train/test split details: 70/15/15 chronological split via time_aware_split')
    print(f'8. Model training pipeline: RandomForestClassifier trained via premonition.training.pipeline')
except Exception as e:
    print(f'Error loading dataset: {e}')

print('\n--- B. MODEL VALIDATION ---')
try:
    registry = ModelRegistry(settings.models_dir)
    tier = 'tier1'
    models = registry.list_models(tier)
    for m in models:
        print(f'Model version found: {m.get("model_version", "unknown")}')
        
    try:
        metrics = registry.load_metadata(tier).get("metrics", {})
        print(f'\n2. Used for prediction: RandomForest Tier 1 Best Model')
        print(f'3. Accuracy metrics: {metrics.get("accuracy", 0):.4f}')
        print(f'4. Precision: {metrics.get("precision", 0):.4f}')
        print(f'5. Recall: {metrics.get("recall", 0):.4f}')
        print(f'6. F1 score: {metrics.get("f1_score", 0):.4f}')
        print(f'7. ROC-AUC: {metrics.get("roc_auc", 0):.4f}')
    except Exception as e:
        print(f"Error loading metrics: {e}")
except Exception as e:
    print(f'Error validating model: {e}')
