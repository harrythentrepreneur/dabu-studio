# RunPod Worker Dockerfile
# Heavy processing container with FFmpeg, Python, and ML dependencies

FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Install system dependencies including FFmpeg with GPU support
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3-pip \
    ffmpeg \
    wget \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy handler code
COPY handler.py .
COPY gemini_processor.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=video,compute,utility

# Create temp directory
RUN mkdir -p /tmp/processing

# RunPod expects the handler to be run directly
CMD ["python3", "-u", "handler.py"]