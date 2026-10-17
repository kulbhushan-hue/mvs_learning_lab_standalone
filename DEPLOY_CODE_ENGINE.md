# Deploy the MVS Learning Lab to IBM Cloud Code Engine

This guide deploys the standalone Streamlit learning app.

## Prerequisites

- An IBM Cloud account with Code Engine and Container Registry access.
- The IBM Cloud CLI and Code Engine/Container Registry plug-ins.
- Docker or a Code Engine build source supported by your account.
- Optional watsonx.ai project or space, API key, region endpoint, and model
  access if you want Granite-generated tutor answers.

The app works without watsonx.ai credentials; its lessons and TF-IDF retrieval
are local.

## Build and run locally

```sh
python -m pip install -r requirements.txt
streamlit run app.py
```

Or build and test the container:

```sh
docker build -t mvs-learning-lab:1 .
docker run --rm -p 8080:8080 mvs-learning-lab:1
```

Open `http://localhost:8080`. The included Dockerfile runs Streamlit on port
8080.

## Deploy from source

```sh
ibmcloud login --sso
ibmcloud target -r us-south -g <resource-group>
ibmcloud ce project create --name mvs-learning-lab
ibmcloud ce project select --name mvs-learning-lab
ibmcloud ce application create \
  --name mvs-learning-lab \
  --build-source . \
  --strategy dockerfile \
  --port 8080 \
  --min-scale 1 \
  --cpu 1 \
  --memory 4G
```

Retrieve the application URL:

```sh
ibmcloud ce application get --name mvs-learning-lab --output url
```

Use your organization's approved authentication, TLS, network, and scaling
configuration. Streamlit uses WebSockets, so any proxy in front of the app must
allow WebSocket upgrades and long-lived connections.

## Optional Granite answers

Store credentials in a Code Engine secret, never in the Docker image or source:

```sh
ibmcloud ce secret create --name watsonx-creds \
  --from-literal WATSONX_APIKEY=<api-key> \
  --from-literal WATSONX_PROJECT_ID=<project-id> \
  --from-literal WATSONX_URL=https://us-south.ml.cloud.ibm.com \
  --from-literal WATSONX_MODEL_ID=ibm/granite-3-3-8b-instruct
```

Then attach the secret to the application:

```sh
ibmcloud ce application update \
  --name mvs-learning-lab \
  --env-from-secret watsonx-creds
```

Use `WATSONX_SPACE_ID` instead of `WATSONX_PROJECT_ID` when using a deployment
space. Confirm that the model is enabled in that project/space and that outbound
HTTPS to the selected watsonx.ai endpoint is allowed.
