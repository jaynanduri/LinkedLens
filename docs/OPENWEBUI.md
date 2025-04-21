## OpenwebUI

![Demo](/images/Demo.gif)

We are using customized version of [OpenwebUI](https://github.com/open-webui/open-webui), open-source project for chat applications. The customization includes:
- **Main feed**: LinkedIn-like feed for displaying recent posts and job listings `src/routes/linkedin`.
- **Job Posting Page**: displaying job details, description, and a button to apply for the job `src/routes/jobs`.
- **User and Recruiter Post Pages**: displaying the user-generated content on the website `src/routes/posts`.
- **LinkedLens Agent Function**: calling our workflow endpoint, handling the user interaction, enforcing guardrails.

## Database

We utilize a **PostgreSQL** database to store application data. The primary tables relevant to the core *functionality*, *monitoring* and *evaluation*:

- **`chat`** table schema (truncated):
  - `id`: varchar(255)
  - `user_id`: varchar(255)
  - `title`: text
  - `created_at`: datetime
  - `chat`: json
  - ...

- **`feedback`** table schema (truncated):
  - `id`: text
  - `user_id`: text
  - `data`: json
  - `meta`: json
  - `snapshot`: json
  - `created_at`: datetime
  - ...

## Deployment

The OpenWebUI deployment is done on the same cluster as the model-development pipeline. The script [open-webui/k8s-run.sh](https://github.com/jaynanduri/open-webui/blob/main/k8s-run.sh) can be used to setup Kubernetes service account, along with its annotation ( for keyless authentication for Firestore access), Kubernetes deployment, and creating persistent volume claims, and a LoadBalancer service ([K8s Manifests](https://github.com/jaynanduri/open-webui/tree/main/kubernetes/frontend)). The script also builds and pushes a docker image to the Artifact Registry.

The deployement is set to have 1 replica with a `rollingUpdate` strategy (`maxSurge:1, maxUnavailable:1`). The service endpoint uses a static IP and exposes the port 80 externally. A persistent volume claim of 2Gi is also created. 

The deployment is hosted at: [http://linkedlens.duckdns.org/](http://linkedlens.duckdns.org/)