# Containerized test runner for SynapseQA.
#
# Build:
#   docker build -t synapseqa-tests .
#
# Run (join the OrangeHRM compose network so "orangehrm" resolves by service name;
# the project name below matches the infra/ directory unless overridden):
#   docker compose -f infra/docker-compose.orangehrm.yml up -d --wait
#   docker run --rm --network infra_default \
#     -e TEST_ORANGEHRM_URL=http://orangehrm:80 \
#     -e TEST_ADMIN_USERNAME=<username> -e TEST_ADMIN_PASSWORD=<password> \
#     synapseqa-tests -m smoke

FROM mcr.microsoft.com/playwright/python@sha256:684df257a1fa0ef3fa288239819984008f560e8f8db5b635ee9e2a50cbcd2e23

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /uvx /usr/local/bin/

# Dependencies first so this layer is cached across source-only changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY . .
RUN uv sync --locked

ENTRYPOINT ["uv", "run", "pytest"]
CMD ["-m", "smoke"]
