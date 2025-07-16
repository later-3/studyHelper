# Dockerfile for StudyHelper (v6 - Final with Vim)

# 1. Start from a stable, official Python base image.
FROM python:3.11-slim-bookworm

# 2. Set environment variables.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV HF_ENDPOINT=https://hf-mirror.com

# 3. Set up the working directory.
WORKDIR /app

# 4. Install all system dependencies required by our Python packages.
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    vim \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Configure pip to use a mirror in China permanently.
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 6. Copy requirements.txt and install all Python packages.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# 7. Copy the model download script and run it.
COPY scripts/download_models.py scripts/download_models.py
RUN python scripts/download_models.py

# 7.5. 预下载PaddleOCR中文模型，避免运行时卡顿
RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='ch')"

# 8. Copy the rest of the project code.
COPY . .

# 9. Install the project itself as a package.
RUN pip install -e .

# 10. Expose the port Streamlit will run on.
EXPOSE 8501

# 11. Define the default command to run when the container starts.
CMD ["streamlit", "run", "apps/app_v2.py", "--server.port=8501", "--server.address=0.0.0.0"]