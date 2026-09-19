# Reviewer Recommendation API

A FastAPI service that recommends reviewers for a submitted research-paper PDF. It builds a profile for each reviewer from their existing papers, then ranks profiles by semantic similarity to the uploaded paper.

## How it works

1. The dataset contains one directory per reviewer, each with one or more PDF papers.
2. Text is extracted from each paper and its title and abstract are identified.
3. The service uses the `all-MiniLM-L6-v2` Sentence Transformers model to create an average embedding for every reviewer.
4. When a PDF is submitted to `/rank`, the API returns the five reviewers with the closest profiles.

## Requirements

- Python 3.10 or later
- A reviewer dataset organized as shown below

```text
Dataset/
|-- reviewer-a/
|   |-- paper-one.pdf
|   `-- paper-two.pdf
`-- reviewer-b/
    `-- paper-three.pdf
```

Install the dependencies:

```powershell
pip install fastapi "uvicorn[standard]" pydantic-settings pypdf numpy sentence-transformers python-multipart
```

## Configuration

Set the `DATASET_PATH` environment variable to the directory containing reviewer folders. You can place it in a `.env` file at the project root:

```env
DATASET_PATH=C:/path/to/Dataset
```

If `DATASET_PATH` is not set, the app uses the local default configured in `app/core/config.py`. Using an environment variable is recommended so the path is portable.

## Run locally

```powershell
uvicorn app.main:app --reload
```

The API starts at `http://127.0.0.1:8000`. Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Lists the total indexed papers and up to the first 10 entries. |
| `GET` | `/test-extraction/{paper_number}` | Returns the detected title, abstract, and keywords for an indexed paper. |
| `GET` | `/debug-paper/{paper_number}` | Returns the first 2,500 extracted characters for troubleshooting. |
| `POST` | `/rank` | Accepts a PDF form upload and returns the top five reviewer recommendations. |

### Rank a paper

```powershell
curl.exe -X POST "http://127.0.0.1:8000/rank" -F "file=@C:/path/to/submission.pdf"
```

Example response:

```json
{
  "filename": "submission.pdf",
  "top_reviewers": [
    {"reviewer": "reviewer-a", "score": 0.82},
    {"reviewer": "reviewer-b", "score": 0.74}
  ]
}
```

## Notes

- Reviewer profiles are built on the first ranking request and cached in memory for the lifetime of the process. The initial request can take longer for a large dataset.
- The embedding model downloads automatically on its first use, so an internet connection may be needed initially.
- PDFs must contain extractable text; scanned PDFs without OCR may produce poor or empty results.
