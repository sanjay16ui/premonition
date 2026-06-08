# Backup Strategy

## What Gets Backed Up

| Directory | Contents | Priority |
|-----------|----------|----------|
| `models/artifacts/` | Trained models + preprocessors | Critical |
| `reports/` | Training metrics, SHAP plots, patient reports | High |
| `logs/` | Application logs + prediction audit trail | High |
| `data/processed/` | Train/val/test splits + quality reports | Medium |
| `src/premonition/config/` | Feature tiers + model config | Medium |

---

## How to Backup

### Windows
```powershell
.\scripts\backup.ps1
```

### Linux/macOS
```bash
bash scripts/backup.sh
```

### Makefile
```bash
make backup
```

---

## Backup Output

```
backups/
├── premonition_backup_20260605_140000.zip   # Windows
└── premonition_backup_20260605_140000.tar.gz # Linux
```

Each archive contains a `manifest.json` with timestamp and contents list.

---

## Retention

- **Last 10 backups** kept automatically
- Older backups deleted on each new backup run
- Prediction logs rotate daily (90-day retention via `logging.yaml`)

---

## Restore Procedure

1. Stop any running training/prediction processes
2. Extract archive: `tar -xzf backups/premonition_backup_*.tar.gz`
3. Copy contents back to project root:
   ```bash
   cp -r backup_*/models/artifacts/* models/artifacts/
   cp -r backup_*/reports/* reports/
   cp -r backup_*/logs/* logs/
   ```
4. Verify: `python -c "from premonition.models import ModelRegistry; ModelRegistry('models/artifacts').load_best_model('t1')"`

---

## Recommended Schedule

| Environment | Frequency | Method |
|-------------|-----------|--------|
| Development | Before each retrain | Manual `backup.ps1` |
| Staging | Daily (cron) | `bash scripts/backup.sh` |
| Production | Daily + pre-deploy | Cron + CI/CD artifact storage |
