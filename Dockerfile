# Use a slim base image
:contentReference[oaicite:1]{index=1}

# Prevent Python from writing .pyc files and enable unbuffered logs
:contentReference[oaicite:2]{index=2} \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy and install dependencies
:contentReference[oaicite:3]{index=3}
:contentReference[oaicite:4]{index=4}

# Copy your application code
COPY . .

# Expose the port your app listens on
EXPOSE 8080

# Run with Gunicorn for production stability
:contentReference[oaicite:5]{index=5}
