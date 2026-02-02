# Multi-stage Production Dockerfile for Next.js Frontend
# Stage 1: Dependencies - install dependencies
# Stage 2: Builder - build the application
# Stage 3: Runner - run the production build

# ======================
# Stage 1: Dependencies
# ======================
FROM node:20-alpine AS deps

# Check https://github.com/nodejs/docker-node/tree/main/docs/BestPractices.md
# for information on security best practices
RUN apk add --no-cache libc6-compat

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
# Using --omit=dev to skip devDependencies in production
RUN npm ci --legacy-peer-deps

# ======================
# Stage 2: Builder
# ======================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy application code
COPY . .

# Set production environment variable
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Build the application
# This creates an optimized production build in .next directory
RUN npm run build

# ======================
# Stage 3: Runner
# ======================
FROM node:20-alpine AS runner

WORKDIR /app

# Set environment to production
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Change ownership to non-root user
RUN chown -R nextjs:nodejs /app

# Switch to non-root user
USER nextjs

# Expose port 3000
EXPOSE 3000

# Set hostname for Next.js server
ENV HOSTNAME="0.0.0.0"
ENV PORT=3000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

# Start the application
CMD ["node", "server.js"]