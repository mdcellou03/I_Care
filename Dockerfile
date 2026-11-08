# Same Python minor version the model was exported with (see .python-version).
FROM python:3.13-slim

# OpenCV needs these system libraries even though we never open a window.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces runs containers as a non-root user with id 1000.
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH" \
    PYTHONUNBUFFERED=1
WORKDIR /home/user/app

# CPU-only torch first: the default build bundles GPU libraries we can't use (gigabytes).
RUN pip install --no-cache-dir --user torch==2.15.0 torchvision \
    --index-url https://download.pytorch.org/whl/cpu

# Then the rest of the backend dependencies (torch is already satisfied).
COPY --chown=user backend/requirement.txt backend/requirement.txt
RUN pip install --no-cache-dir --user -r backend/requirement.txt

# Only what the server needs: API, frontend, model and the two ML helpers. No datasets.
COPY --chown=user backend/app backend/app
COPY --chown=user frontend frontend
COPY --chown=user ml/models ml/models
COPY --chown=user ml/recommendation.py ml/validate_image.py ml/

WORKDIR /home/user/app/backend
EXPOSE 7860
# 0.0.0.0 = accept connections from outside the container; 7860 is the port Spaces expects.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]