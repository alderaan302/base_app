FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

ENV SETTINGS_DIR=/data

# Install SSH client, sshpass, Chrome and ChromeDriver for Selenium
RUN apt-get update && apt-get install -y \
    openssh-client \
    sshpass \
    wget \
    gnupg \
    unzip \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set up Chrome/Chromium for Selenium
ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    PATH="/usr/bin:${PATH}"

# Create symbolic links to ensure Selenium finds the driver
RUN ln -sf /usr/bin/chromedriver /usr/local/bin/chromedriver || true

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

EXPOSE 8084

CMD ["gunicorn", "--bind", "0.0.0.0:8084", "--timeout", "120", "--workers", "2", "app:app"]
