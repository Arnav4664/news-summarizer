# Use Python official image
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy all project files
COPY . /app

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI backend
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
