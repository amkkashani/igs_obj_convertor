# Start from a slim Python 3.10 image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# --- NEW: Install Docker Client ---
# 1. Update package lists
# 2. Install dependencies needed for Docker's apt repository
# 3. Add Docker's official GPG key
# 4. Set up the Docker repository
# 5. Install the Docker client (docker-ce-cli)
RUN apt-get update && \
    apt-get install -y ca-certificates curl gnupg && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli
# --- End of new section ---

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code (main.py, static/ folder)
COPY . .

# Expose the port the app will run on
EXPOSE 8000

# Command to run the application
# uvicorn main:app tells uvicorn to run the 'app' object from the 'main.py' file
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]