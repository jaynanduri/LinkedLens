### Deploying Cloud Run Functions

- Build the DOCKERFILE ([follow guide to deploy container images](https://cloud.google.com/run/docs/deploying)) or alternatively copy contents as Inline Google Run Function on Console
- Setup and connect a VPC connector
  - The funciton triggers a DAG hosted on a Compute Engine. To connect to this, make sure that VPC Network is enabled
  - Setup a VPC network using `gcloud` or using Console (Clound Run -> Service -> Edit & Deploy Revision -> Networks)
  - Make sure appropriate roles and IAM is setup
- Setup a Trigger for Firestore. Make sure the region and firestore DB name are correct. Use the Eventrac trigger `google.cloud.firestore.entity.v1.written` for the current trigger. This triggers the function every time there is a change to a document.
- Before running: check [required APIs and roles](https://cloud.google.com/run/docs/triggering/firestore-triggers#before_you_begin)
