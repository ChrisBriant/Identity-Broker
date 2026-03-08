# Identity Broker (FastAPI)

A lightweight **Identity Broker** built with FastAPI that supports authentication through multiple external Identity Providers (IDPs) and issues a unified application JWT for clients.

This project demonstrates how a backend service can act as an **authentication gateway**, normalising authentication across multiple providers such as:

- :contentReference[oaicite:0]{index=0}
- :contentReference[oaicite:1]{index=1}
- :contentReference[oaicite:2]{index=2}

The broker performs the OAuth/OpenID Connect flow with external providers, retrieves user identity information, and issues its own JWT used by downstream applications.

---

## Overview

Modern applications often allow users to authenticate using third-party identity providers. Integrating multiple providers directly into each frontend can lead to duplication and inconsistent security logic.

This project demonstrates a **broker pattern**, where a backend service:

1. Initiates authentication with external IDPs  
2. Handles OAuth authorization code exchanges  
3. Retrieves user identity information  
4. Normalises identity data  
5. Issues a single **application JWT**

Client applications (web or mobile) only interact with the broker.

---

## Architecture
User
↓
Client Application (React / Flutter)
↓
Identity Broker (FastAPI)
↓
External Identity Provider
↓
User Identity Returned
↓
Application JWT Issued


## Authentication flow:

1. Client → `/auth/{provider}/login`  
2. Redirect to provider login page  
3. Provider → `/auth/{provider}/callback` with authorization code  
4. Broker → `exchange_code()` → `get_user_info()` → issue JWT

---

## Features

- OAuth / OpenID Connect login flow  
- Multiple identity provider support  
- Provider abstraction layer  
- JWT token issuance  
- User provisioning on first login  
- Modular provider architecture  
- Clean FastAPI router structure  

---

## Project Structure
<!-- app/
│
├── main.py
├── auth/
│ └── routes.py
├── providers/
│ ├── base_provider.py
│ ├── google_provider.py
│ └── provider_registry.py
└── data/ -->


<!-- | Component | Purpose |
|-----------|---------|
| routes    | API endpoints |
| providers | IDP integrations |
| services  | Authentication / business logic |
| models    | Request / response models | -->

---

## Supported Identity Providers

Current providers:

- Google OAuth / OpenID Connect

Planned future providers:

- GitHub OAuth  


The architecture allows new providers to be added with minimal code changes.

---

## Example API Endpoints

### Start authentication

```http
GET /auth/{provider}/login