# StudyBuddy Gemma Fix

This build uses the Google Gen AI Python SDK (`google-genai`) and hosted Gemma 4 models.

- Default: `gemma-4-26b-a4b-it`
- Fallback: `gemma-4-31b-it`

API-key validation now checks model metadata with `client.models.get()` instead of requiring a tiny prompt to return text. Generated responses also extract text from candidate parts when `response.text` is empty and report useful block/finish diagnostics.

Install once with:

```text
python -m pip install -r requirements.txt
```

Then restart Streamlit.
