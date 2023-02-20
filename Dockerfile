# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container and install the dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the exporter files into the container
COPY exporter.py .

# Copy the rest of the application code into the container at /app
COPY . .

# Copy the config.yaml file into the container at /app
COPY config.yaml .

# Expose port 8000 for the exporter to listen on
EXPOSE 8000

# Run the exporter script when the container starts
CMD ["python", "exporter.py"]
