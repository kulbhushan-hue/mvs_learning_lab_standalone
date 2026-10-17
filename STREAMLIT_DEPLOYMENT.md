# MVS SYSPROG Learning Lab

This is a standalone Streamlit app for learning z/OS concepts.

## Run locally

From this folder, run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On macOS/Linux, activate the environment with
`source .venv/bin/activate` and start it with `streamlit run app.py`.

## Deploy to Streamlit Community Cloud

1. Push this folder's app files to a GitHub repository.
2. Create an app in Streamlit Community Cloud, select the repository and branch,
   and set the main file path to `app.py`.
3. Deploy. Streamlit installs dependencies from `requirements.txt`.
4. Open the app and try `HELP`, `LISTCAT`, `ISPF`, `SDSF`, `D A`, and `SUBMIT`.

Keep `app.py`, `zos_learning_lab.py`, `requirements.txt`, and `Dockerfile`
together. The retrieval index is built locally from the lesson corpus and can be
downloaded from the tutor as a `.joblib` file. Do not load joblib files from
untrusted sources.

## Optional watsonx.ai Granite tutor

The lessons and local TF-IDF retrieval work without cloud credentials. To enable
generated answers, configure Streamlit secrets:

```toml
WATSONX_APIKEY = "your-IBM-Cloud-API-key"
WATSONX_PROJECT_ID = "your-watsonx-project-id"
WATSONX_URL = "https://us-south.ml.cloud.ibm.com"
WATSONX_MODEL_ID = "ibm/granite-3-3-8b-instruct"
```

Use either `WATSONX_PROJECT_ID` or `WATSONX_SPACE_ID`. Set secrets in the
deployment platform, never in source code. The selected project/space must have
access to the chosen model and regional endpoint.

## Safety and certificate

The 3270-style console is a local simulator. It has no host connection and never
submits JCL or changes a z/OS system. SMP/E examples contain placeholders and
are for a disposable sandbox only; confirm procedures against IBM documentation
and site change controls.

The quiz certificate is an unofficial learning certificate, not issued or
endorsed by IBM. A learner may upload a PNG/JPG logo they are authorized to use.
