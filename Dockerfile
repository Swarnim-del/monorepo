FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies using uv sync
# --frozen ensures we use the exact versions in uv.lock
# --no-dev skips installing development dependencies
RUN uv sync

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Expose port 8000
EXPOSE 8000 


# Change to the source directory where manage.py and config are located
WORKDIR /app/src

# Run the development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
