# turath-inveniordm

Welcome to your InvenioRDM instance.

## Getting started

Run the following commands in order to start your new InvenioRDM instance:

```console
invenio-cli containers start --lock --build --setup
```

The above command first builds the application docker image and afterwards
starts the application and related services (database, Opensearch, Redis
and RabbitMQ). The build and boot process will take some time to complete,
especially the first time as docker images have to be downloaded during the
process.

Once running, visit https://127.0.0.1 in your browser.

**Note**: The server is using a self-signed SSL certificate, so your browser
will issue a warning that you will have to by-pass.

## Overview

Following is an overview of the generated files and folders:

| Name | Description |
|---|---|
| ``Dockerfile`` | Dockerfile used to build your application image. |
| ``Pipfile`` | Python requirements installed via [pipenv](https://pipenv.pypa.io) |
| ``Pipfile.lock`` | Locked requirements (generated on first install). |
| ``app_data`` | Application data such as vocabularies. |
| ``assets`` | Web assets (CSS, JavaScript, LESS, JSX templates) used in the Webpack build. |
| ``docker`` | Example configuration for NGINX and uWSGI. |
| ``docker-compose.full.yml`` | Example of a full infrastructure stack. |
| ``docker-compose.yml`` | Backend services needed for local development. |
| ``docker-services.yml`` | Common services for the Docker Compose files. |
| ``invenio.cfg`` | The Invenio application configuration. |
| ``logs`` | Log files. |
| ``static`` | Static files that need to be served as-is (e.g. images). |
| ``templates`` | Folder for your Jinja templates. |
| ``.invenio`` | Common file used by Invenio-CLI to be version controlled. |
| ``.invenio.private`` | Private file used by Invenio-CLI *not* to be version controlled. |

## Additional Services

This repository includes additional services for IIIF support and local development:

| Service | Port | Purpose |
|---------|------|---------|
| **Cantaloupe** | 8182 | IIIF Image API server for book page images |
| **MinIO** | 9000, 9001 | S3-compatible object storage (local development) |
| **OpenSearch Dashboards** | 5601 | Search index exploration UI |
| **pgAdmin** | 5050 | PostgreSQL database administration |

## CI/CD and Deployment

This repository uses GitHub Actions for continuous integration and deployment. For detailed information:

- **[Architecture Clarification](.github/ARCHITECTURE-CLARIFICATION.md)** - ⭐ **START HERE**: Understanding Local vs Production deployment
- **[CI/CD Documentation](.github/CICD.md)** - Complete CI/CD workflow documentation
- **[CI/CD Quick Start](.github/CICD-QUICKSTART.md)** - Quick reference for common operations
- **[Differences from Upstream](.github/DIFFERENCES-FROM-UPSTREAM.md)** - Local dev vs production architecture

**Key Point**: Local development uses Docker containers for all services (PostgreSQL, OpenSearch, S3/MinIO). Production deployment (via Terraform) uses AWS managed services (RDS, OpenSearch Service, S3). See [Architecture Clarification](.github/ARCHITECTURE-CLARIFICATION.md) for details.

### Quick Start

**Pull latest images:**
```bash
docker pull ghcr.io/OWNER/turath-rdm:main
docker pull ghcr.io/OWNER/turath-rdm-frontend:main
```

**Trigger a build:**
```bash
git push origin main  # Builds and pushes images
```

## Documentation

To learn how to configure, customize, deploy and much more, visit
the [InvenioRDM Documentation](https://inveniordm.docs.cern.ch/).
