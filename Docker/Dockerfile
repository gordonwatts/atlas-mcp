FROM sslhep/rucio-client:main

# Update everything
RUN yum update -y

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create user where we will run the MCP tool.
RUN useradd -u 1000 -m -s /bin/bash MCPAtlas

# Configure for GRID, etc.
ENV PYTHONUNBUFFERED=1
ENV X509_USER_PROXY=/tmp/x509up
ENV HOME=/home/MCPAtlas

# Ensure MCPAtlas user owns their home directory
RUN chown -R MCPAtlas:MCPAtlas /home/MCPAtlas
WORKDIR /home/MCPAtlas

# Switch to mcp user.
USER MCPAtlas