# KHC Python Services

This folder contains all Python-based services for the **KHC** system.

## 📁 Structure

```
python/
├── pyproject.toml      ← package metadata
└── src/
    └── khc/
        ├── __init__.py
        └── services/
            ├── __init__.py
            ├── common.py
            └── mac_mini/
                ├── __init__.py
                └── khc_mqtt_to_kvm.py
```

Each subfolder under `services/` is one self-contained module (e.g. `mac_mini`, `shield_remote`, etc.).

---

## 🧱 Setup (one-time)

1. **Create a virtual environment**
   ```bash
   cd ~/khc/python
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Upgrade the toolchain**
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

3. **Install in editable mode**
   ```bash
   pip install -e .
   ```

This makes the `khc` package importable anywhere on the system.

---

## ▶️ Running a Service

From inside the `python` folder (or anywhere once installed):

```bash
python -m khc.services.mac_mini.khc_mqtt_to_kvm
```

If you don’t want to activate the venv every time:

```bash
~/khc/python/.venv/bin/python -m khc.services.mac_mini.khc_mqtt_to_kvm
```

---

## 🧹 Housekeeping

- To update dependencies later:  
  ```bash
  pip install --upgrade -r requirements.txt
  ```
  *(if you add such a file)*

- To remove build artefacts:  
  ```bash
  rm -rf build dist *.egg-info
  ```

- To leave the venv:  
  ```bash
  deactivate
  ```

---

## 💡 Developer Notes

- Use **absolute imports** (`from khc.services.common import ...`) not relative imports.
- All service folders must contain an `__init__.py`.
- Avoid hyphens in filenames and folders (`mac_mini` ✅  not `mac-mini` ❌).
- Never commit `.venv/` or `__pycache__/`.

---

*(End of README)*
