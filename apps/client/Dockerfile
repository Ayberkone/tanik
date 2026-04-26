# syntax=docker/dockerfile:1.7

# Multi-stage build of the TANIK Next.js client.
# Producing a `standalone` Next.js bundle (next.config.ts → output: "standalone")
# means the runtime stage ships only the server.js + .next/standalone deps it
# actually needs, not all of node_modules.

# ============================================================================
# Stage 1 — deps: install all node_modules (including dev) for the build.
# ============================================================================
FROM node:24-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# ============================================================================
# Stage 2 — builder: produce the .next/standalone bundle.
# ============================================================================
FROM node:24-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Disable Next telemetry — operator privacy for the kiosk deployment.
ENV NEXT_TELEMETRY_DISABLED=1

# Opt into the standalone Next.js output (next.config.ts gates on this env
# var). Vercel deploys leave this unset so they get a normal serverless
# build; Docker deploys turn it on so the runtime stage can ship the
# minimal .next/standalone/ bundle.
ENV BUILD_STANDALONE=true

# NEXT_PUBLIC_API_BASE_URL must be set at build time because Next bakes it
# into the client bundle. Pass via --build-arg or the compose service env.
ARG NEXT_PUBLIC_API_BASE_URL=http://inference:8000
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

RUN npm run build

# ============================================================================
# Stage 3 — runtime: minimal image with the standalone server only.
# ============================================================================
FROM node:24-alpine AS runtime
WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0 \
    NEXT_TELEMETRY_DISABLED=1

# Non-root user — matches the backend image's posture.
RUN addgroup --system --gid 1001 nodejs \
 && adduser --system --uid 1001 nextjs

# Copy the standalone bundle + the static assets Next splits out.
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:3000/ || exit 1

CMD ["node", "server.js"]
