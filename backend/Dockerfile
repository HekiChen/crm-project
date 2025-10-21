FROM continuumio/miniconda3:latest

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Update conda and install mamba for faster package resolution
RUN conda update -n base -c defaults conda \
    && conda install -n base -c conda-forge mamba \
    && conda clean -afy

# Copy environment file
COPY environment.yml .

# Create conda environment using mamba
RUN mamba env create -f environment.yml \
    && conda clean -afy

# Make RUN commands use the new environment
SHELL ["conda", "run", "-n", "crm-backend", "/bin/bash", "-c"]

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["conda", "run", "--no-capture-output", "-n", "crm-backend", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]