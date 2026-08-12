# Videoflix Backend

A Django REST Framework backend for Videoflix, a video streaming platform. The
project provides a cookie-based JWT authentication system, background task
processing via Django RQ, and Redis caching, all running through Docker.

> **Status:** Authentication (registration, activation, login, logout, token
> refresh, password reset) and video delivery (listing, HLS playlist and
> segment streaming, background HLS conversion) are complete.

## Table of Contents

- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [Installing FFmpeg](#installing-ffmpeg)
  - [Installation & Setup](#installation--setup)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [HLS Video Delivery](#hls-video-delivery)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [Notes](#notes)
- [License](#license)
- [Author](#author)

## Tech Stack

- **Framework:** Django 6.0 + Django REST Framework
- **Database:** PostgreSQL
- **Cache:** Redis (via `django-redis`)
- **Background Tasks:** Django RQ
- **Auth:** JSON Web Tokens (`djangorestframework-simplejwt`), delivered as
  HttpOnly cookies
- **Web Server:** Gunicorn
- **Static Files:** WhiteNoise
- **Containerization:** Docker & Docker Compose
- **Video Processing:** FFmpeg (HLS conversion), Pillow (thumbnail image validation)
- **Testing:** Django APITestCase

## Prerequisites

- Docker
- Docker Compose

## Getting Started
### Installing FFmpeg

FFmpeg is required for converting uploaded videos into HLS format (480p,
720p, 1080p) with `.m3u8` playlists and `.ts` segments. Since the project
runs entirely through Docker, FFmpeg does **not** need to be installed on
your host machine — it is already included in the `web` container's Alpine
image (installed via `apk` in the Dockerfile).

Local installation is only needed if you want to run the conversion logic
directly outside Docker (e.g. for debugging).

#### Windows

Using Winget (recommended):

```bash
winget install --id Gyan.FFmpeg -e --source winget
```

Or download the latest build from:

https://ffmpeg.org/download.html

After installation, make sure the `ffmpeg` executable is available in your system's `PATH`.

#### macOS

Using Homebrew:

```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install ffmpeg
```

Verify the installation:

```bash
ffmpeg -version
```

### Installation & Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/PatLiCoding/Videoflix.git
   cd videoflix-backend
   ```

2. **Create an `.env` file** in the project root (see [Environment
   Variables](#environment-variables) below for all available options).
> **Note:** The `EMAIL_*` values in `.env.template` are placeholders. See
> [Notes](#notes) for what happens if you don't replace them with real SMTP
> credentials.
   ```bash
   cp .env.template .env
   ```

3. **Start the project**

   ```bash
   docker compose up --build
   ```

   This builds the images and starts three services:
   - `db` – PostgreSQL database
   - `redis` – Redis cache and RQ broker
   - `web` – Django application (via `entrypoint.sh`)

   On startup, `entrypoint.sh` automatically:
   - waits for PostgreSQL to become available
   - runs `collectstatic`, `makemigrations`, and `migrate`
   - creates a superuser from environment variables (if one doesn't exist yet)
   - starts an RQ worker for background email jobs
   - starts the Gunicorn server on `0.0.0.0:8000`

4. **Access the API** at `http://localhost:8000/api/`

## Environment Variables

| Variable                    | Description                                                    | Default                                       |
| --------------------------- | -------------------------------------------------------------- | --------------------------------------------- |
| `SECRET_KEY`                | Django secret key                                              | insecure dev key                              |
| `DEBUG`                     | Enable Django debug mode                                       | `False`                                       |
| `ALLOWED_HOSTS`             | Comma-separated list of allowed hosts                          | `localhost`                                   |
| `CSRF_TRUSTED_ORIGINS`      | Comma-separated list of trusted origins for CSRF               | `http://localhost:4200`                       |
| `CORS_ALLOWED_ORIGINS`      | Comma-separated list of allowed CORS origins                   | `http://127.0.0.1:5500,http://localhost:5500` |
| `FRONTEND_URL`              | Base URL of the frontend, used to build activation/reset links | `http://localhost:5500`                       |
| `DB_NAME`                   | PostgreSQL database name                                       | `videoflix_db`                                |
| `DB_USER`                   | PostgreSQL user                                                | `videoflix_user`                              |
| `DB_PASSWORD`               | PostgreSQL password                                            | —                                             |
| `DB_HOST`                   | PostgreSQL host                                                | `db`                                          |
| `DB_PORT`                   | PostgreSQL port                                                | `5432`                                        |
| `REDIS_LOCATION`            | Redis connection URL for the cache backend                     | `redis://redis:6379/1`                        |
| `REDIS_HOST`                | Redis host for the RQ queue                                    | `redis`                                       |
| `REDIS_PORT`                | Redis port for the RQ queue                                    | `6379`                                        |
| `REDIS_DB`                  | Redis DB index for the RQ queue                                | `0`                                           |
| `EMAIL_HOST`                | SMTP host for outgoing email                                   | —                                             |
| `EMAIL_PORT`                | SMTP port                                                      | `587`                                         |
| `EMAIL_HOST_USER`           | SMTP username                                                  | —                                             |
| `EMAIL_HOST_PASSWORD`       | SMTP password                                                  | —                                             |
| `EMAIL_USE_TLS`             | Use TLS for SMTP                                               | `True`                                        |
| `EMAIL_USE_SSL`             | Use SSL for SMTP                                               | `False`                                       |
| `DEFAULT_FROM_EMAIL`        | Sender address for outgoing emails                             | —                                             |
| `DJANGO_SUPERUSER_USERNAME` | Username for the auto-created superuser                        | `admin`                                       |
| `DJANGO_SUPERUSER_EMAIL`    | Email for the auto-created superuser                           | `admin@example.com`                           |
| `DJANGO_SUPERUSER_PASSWORD` | Password for the auto-created superuser                        | `adminpassword`                               |

## API Endpoints

All endpoints are prefixed with `/api/`. Authentication is handled via
HttpOnly cookies (`access_token`, `refresh_token`) set by the server — the
frontend does not need to manage tokens manually.

| Method | Endpoint                                    | Description                                                 | Auth required  |
| ------ | ------------------------------------------- | ----------------------------------------------------------- | -------------- |
| POST   | `/register/`                                | Register a new (inactive) user and send an activation email | No             |
| GET    | `/activate/<uidb64>/<token>/`               | Activate a user account via the emailed link                | No             |
| POST   | `/login/`                                   | Authenticate and receive JWT auth cookies                   | No             |
| POST   | `/logout/`                                  | Blacklist the refresh token and clear auth cookies          | No             |
| POST   | `/token/refresh/`                           | Issue a new access token from the refresh token cookie      | Refresh cookie |
| POST   | `/password_reset/`                          | Request a password reset email                              | No             |
| POST   | `/password_confirm/<uidb64>/<token>/`       | Confirm a new password via the emailed link                 | No             |
| GET    | `/video/`                                   | List all available videos                                   | Yes            |
| GET    | `/video/<movie_id>/<resolution>/index.m3u8` | Get the HLS master playlist for a video/resolution          | Yes            |
| GET    | `/video/<movie_id>/<resolution>/<segment>`  | Get a single HLS `.ts` segment                              | Yes            |

## HLS Video Delivery

Videos are converted into HLS (HTTP Live Streaming) format in the background
after upload. Each video is transcoded into three resolutions (480p, 720p,
1080p), each split into `.ts` segments with an accompanying `index.m3u8`
playlist:

```
media/videos/hls/<movie_id>/<resolution>/index.m3u8
media/videos/hls/<movie_id>/<resolution>/000.ts
media/videos/hls/<movie_id>/<resolution>/001.ts
...
```

Conversion is triggered by a `post_save` signal on `Video` creation and runs
asynchronously via Django RQ, so uploading a video does not block the
request. Segment filenames are validated against `\d{3}\.ts` before being
served, to prevent path traversal via the `segment` URL parameter.

## Running Tests

Tests are written with `pytest`/Django's `APITestCase` and cover both
happy-path and unhappy-path (400/401/404) scenarios.

```bash
docker compose exec web python manage.py test
```

or

```bash
docker compose exec web pytest
```

Run tests with coverage:

```bash
docker compose exec web pytest --cov
```

## Project Structure

```
auth_app/
├── models.py           # Custom email-based User model
├── admin.py            # Django admin configuration
├── api/
│   ├── serializers.py  # Request/response validation
│   ├── views.py        # API views (request/response only)
│   └── urls.py          # Auth endpoint routing
└── services/
    ├── auth_services.py     # Login/refresh/logout helper logic
    ├── authentications.py   # Cookie-based JWT authentication class
    ├── decode_uid.py         # UID decoding for activation/reset links
    ├── email_utils.py        # Background email sending via Django RQ
    └── tokens.py              # Activation token generator
```

```
video_content_app/
├── models.py           # Video model (metadata, original file, thumbnail)
├── admin.py            # Django admin configuration
├── api/
│   ├── serializers.py  # Video list serialization
│   ├── views.py        # Video list, HLS playlist, HLS segment views
│   └── urls.py         # Video endpoint routing
└── services/
    ├── tasks.py     # FFmpeg-based HLS conversion, run via Django RQ
    ├── signals.py   # Triggers HLS conversion on video creation
    └── utils.py     # Path resolution and ffmpeg command building
```

## Notes

- The `username` field on the `User` model is unused by the application
  (authentication is entirely email-based) and is kept only for
  compatibility with `entrypoint.sh`, which is a fixed project requirement.
- Password reset and account activation intentionally return generic
  responses/errors to avoid leaking whether an email address is registered.
- To actually receive activation/password-reset emails, replace the
  placeholder `EMAIL_*` values in `.env` with real SMTP credentials (e.g. a
  free [Mailtrap.io](https://mailtrap.io) sandbox works well for testing).
  Without valid credentials, registration/reset requests still return a
  success response, but the email itself will silently fail to send in the
  background worker.
- HLS segment filenames received via the API are validated against a strict
  `\d{3}\.ts` pattern before being read from disk, preventing path traversal
  attacks through the `segment` URL parameter.

## License

This project was developed as part of the Developer Akademie backend course
and serves as a learning project. It is not intended for public deployment.

Frontend repository:
https://github.com/Developer-Akademie-Backendkurs/project.Videoflix

## Author

Developed by **Patricia Linne**
