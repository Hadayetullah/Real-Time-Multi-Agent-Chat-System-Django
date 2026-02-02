# Development Dockerfile for Next.js Frontend
# Optimized for fast rebuild and hot-reloading

FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install dependencies first (Docker layer caching)
# This layer is cached unless package.json or package-lock.json changes
COPY package*.json ./

# Install dependencies
# Using --legacy-peer-deps for compatibility with Next.js 16
RUN npm install --legacy-peer-deps

# Copy application code
# In development, this is usually mounted as a volume
COPY . .

# Expose port 3000 for Next.js
EXPOSE 3000

# Development command with hot-reload
# -H 0.0.0.0 allows connections from outside the container
CMD ["npm", "run", "dev"]