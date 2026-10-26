# Homelab

This mono-repo houses infrastructure, deployment configs and data persitence for various self-hosted personal apps and their dependencies. Everything is managed using Docker Compose and orchestrated with a python CLI automating setup, teardown and disaster recovery.

## Contents

### Orchestration & CLI

Interactions with the orchestration automation are handled via the CLI and justfile.

- Start/restart a service: `just homelab restart pypi`
- Stop a service: `just homelab stop chapflix`
- Stop all services: `just homelab stop-all`
- Full recovery: `just homelab restore`

### Core

#### Postgres

Backend database for various apps

- Version: 16
- Volume: `/media/ianderijk/Backup/postgres-data`
- Ports: 5432
- Dependencies: N/A

#### PyPi

Local pypi index for hosting personal tooling

- Version: latest
- Volume: `/home/idr/packages:/data/packages`
- Ports: 8080
- Dependencies: N/A

### Storage

#### RustFS

s3 compatible object store

- Version: latest
- Volume: internal
- Ports: 9000:9001
- Dependencies: N/A

### Apps

#### Chapflix

Local media streaming app for watching cartoons on weekends

- Version: 2.1.0
- Volume: `home/ianderijk/Backup/Chapflix2/content`
- Ports: 8042
- Dependencies: Chapflix-API

### APIs

#### Chapflix-API

API used in Chapflix backend

- Version: 1.0.0
- Volume: N/A
- Ports: 8043
- Dependencies: Postgres

### Project Management

#### Kaneo

Kanban board used to manage tickets across multiple personal projects

- Version: 2.28.3
- Volume: N/A
- Ports: 5173
- Dependencies: Postgres
