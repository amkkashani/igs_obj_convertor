# Start from a slim Python 3.10 image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

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