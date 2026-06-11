# Monorepo Chat Application

A modern, real-time chat application built with **Django**, **Django Channels** (WebSockets), **Redis**, and **PostgreSQL**, running inside an isolated **Docker** environment.

---

## 🚀 Key Features

* **Real-time Messaging:** Direct, low-latency messaging powered by ASGI, Daphne, and WebSockets (via Django Channels).
* **Robust Auth & Sessions:** Secure user sign-up, login, and session persistence powered by Redis caching.
* **Group Management:** Create private rooms, regenerate secure UUID invitation tokens, and join existing conversations.
* **Production-Ready CI/CD:** Fully automated testing and SSH-based deployment pipelines.
* **Automated SSL Management:** Weekly automated Let's Encrypt certificate renewals via GitHub Actions.

---

## 🛠️ Tech Stack

* **Backend Framework:** Django 5.0+
* **Asynchronous Server (ASGI):** Daphne (ASGI web server for WebSockets)
* **WebSocket Framework:** Django Channels
* **Database (Relational):** PostgreSQL 16 (for chat models, user accounts, and memberships)
* **Caching & Broker:** Redis 7 (for session storage and Channels communication layers)
* **Dependency Manager:** uv (packaged inside Docker)
* **Containerization:** Docker & Docker Compose

---

## 💻 Local Development Setup

### Prerequisites
Make sure you have **Docker** and **Docker Compose** installed on your local machine.

### Running the Application
1. **Clone the repository:**
   ```bash
   git clone <your-repo-url> monorepo
   cd monorepo
   ```

2. **Start the containers:**
   ```bash
   docker compose up --build -d
   ```
   *This command builds the Django image, starts Postgres, Redis, and Web containers, runs database migrations automatically, and starts the development server.*

3. **Access the application:**
   Open your browser and navigate to `http://localhost:8000`.

---

## 🧪 Unit Tests and Code Coverage

We have implemented a comprehensive test suite (scoring **96% code coverage**) covering Django models, views, and async WebSocket consumers (tested using Channels `WebsocketCommunicator`).

To execute the tests and inspect the coverage report inside the running Docker container, run:

```bash
# Run the test suite under the coverage runner
docker compose exec web coverage run --source='chat' manage.py test chat

# View the line-by-line coverage report
docker compose exec web coverage report -m
```

---

## 📡 CI/CD Deployment Architecture

We use **GitHub Actions** for all automation tasks. The workflows are divided into:

1. **Dev Pipeline ([deploy-dev.yml](.github/workflows/deploy-dev.yml)):**
   * **Trigger:** Pushes to the `master` branch.
   * **CI Job:** Launches test services (Postgres, Redis) in the runner and executes the test suite.
   * **CD Job:** If tests pass, SSHs into the Dev server, pulls code, builds, and restarts the Docker containers.

2. **Prod Pipeline ([deploy-prod.yml](.github/workflows/deploy-prod.yml)):**
   * **Trigger:** Pushes to the `production` branch.
   * **CI Job:** Runs the test suite in the runner.
   * **CD Job:** If tests pass, SSHs into the Prod server, pulls code, builds, and restarts the containers.

3. **Certificate Renewal ([renew-certs.yml](.github/workflows/renew-certs.yml)):**
   * **Trigger:** Runs automatically every Sunday at 00:00 UTC (or manually via Workflow Dispatch).
   * **CD Job:** SSHs into the target servers and runs `certbot renew` to ensure SSL certificates never expire.

---

## 🔮 Future Roadmap

* **OAuth Setup:** Connect external identity providers so users can log in via third-party services.
* **User Profiles:** A dedicated page for user customization and status configurations.
* **Separate Databases:** Decouple chat history data from core application accounts.
* **1-to-1 Chat UI-UX:** Dedicated UI upgrades for private direct messaging.
* **Group Chat UI-UX:** Enhanced group views, member management, and invite interfaces.
