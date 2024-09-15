FROM python:3.9-slim

# Setup apt package manager
RUN apt-get update && apt-get install -y git && apt-get clean

# Install pip
RUN pip install --upgrade pip

# Define a work directory in the image
WORKDIR /app

COPY requirements.txt .

# Install all the requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the repo to the image
COPY . .

EXPOSE 50051

CMD ["python", "server.py"]
