## Setting Up Google Kubernetes Engine

1. Create a cluster on GKE
2. Create an Artificat Repository to push Docker images
3. Enable keyless authentication [[Setup](https://cloud.google.com/blog/products/identity-security/enabling-keyless-authentication-from-github-actions)]
    - Along with the service accounts, this project makes use workload identity pools to authenticate GitHub Actions to GCloud.
4. Connect to GitHub Repository to enable CD [[Example Setup]((https://cloud.google.com/dotnet/docs/getting-started/deploying-to-gke-using-github-actions#before-you-begin))]