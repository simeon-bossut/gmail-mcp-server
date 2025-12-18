FROM python:3.12-slim

WORKDIR /app
COPY . .

# Avoid apt-get/uv to keep builds working in restricted networks.
# Install runtime dependencies via pip.
RUN python -c "import tomllib,subprocess; p=tomllib.load(open('pyproject.toml','rb')); deps=p['project']['dependencies']; subprocess.check_call(['pip','install','--no-cache-dir',*deps])"

CMD ["python", "server.py"]