# Run StudyBuddy with one click on Windows

Place these two files in the **same folder as `app.py`**:

- `StudyBuddy Launcher.vbs` — recommended one-click launcher
- `Start StudyBuddy.bat` — fallback/debug launcher

## Recommended

Double-click **`StudyBuddy Launcher.vbs`**.

It will:

1. Find the project folder automatically.
2. Prefer `.venv` or `venv` Python if present.
3. Start Streamlit on port `8501`.
4. Keep the terminal window hidden.
5. Wait for Streamlit to become available.
6. Open StudyBuddy in Google Chrome when Chrome is installed.
7. Fall back to the default browser if Chrome is unavailable.

No terminal command is required.

## Requirements

Python and the project's Python dependencies still need to be installed **once** on a local computer. The launcher does not install Python or project dependencies.

The launcher assumes the main Streamlit entry point is:

```text
app.py
```

For the deployed Streamlit Cloud version, users can simply open the application's web URL.
