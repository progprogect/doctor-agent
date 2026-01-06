# Frontend Dockerfile для Next.js
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
# Используем mount cache для npm (требует BuildKit)
# Это ускорит установку зависимостей при повторных сборках
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set environment variables for build
ENV NEXT_TELEMETRY_DISABLED 1
ENV NODE_ENV production

# Build Next.js
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Install curl for health checks
RUN apk add --no-cache curl

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
# In standalone mode, Next.js creates a self-contained app in .next/standalone
# The standalone directory structure:
#   .next/standalone/
#     ├── server.js
#     ├── .next/static/ (already included)
#     └── node_modules/
# We need to copy public files and static files separately for optimization
COPY --from=builder /app/public ./public

# Copy standalone output (contains server.js, node_modules, and basic structure)
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./

# Copy static files - they need to be at .next/static relative to server.js
# The standalone directory may have an empty .next/static, so we overwrite it
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]





