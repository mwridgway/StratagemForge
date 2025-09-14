# Multi-stage build for Node.js BFF service
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Development dependencies for building
FROM base AS build-deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# Build the application
FROM build-deps AS builder
WORKDIR /app
COPY . .

# Fix permissions and build TypeScript
RUN chmod +x node_modules/.bin/* && \
    npm run build

# Production image
FROM base AS runner
WORKDIR /app

# Create app user for security
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 bff

# Copy built application
COPY --from=builder --chown=bff:nodejs /app/dist ./dist
COPY --from=deps --chown=bff:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=bff:nodejs /app/package.json ./package.json

# Switch to app user
USER bff

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:8080/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) }).on('error', () => process.exit(1))"

# Start the application
CMD ["node", "dist/index.js"]