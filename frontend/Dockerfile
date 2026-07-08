# ==============================================================================
# Frontend Dockerfile — Multi-Stage Build
#
# Stage 1 (builder): Install dependencies and build the React app
# Stage 2 (nginx):   Serve the static build output with Nginx
#
# WHY multi-stage?
# The final image only contains the Nginx server + built static files.
# Node.js, npm, source code, and node_modules are NOT in the final image.
# Result: production image is ~25MB instead of ~500MB.
# ==============================================================================

# Stage 1 — Build the React application
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first (separate Docker layer for caching)
# If package.json hasn't changed, npm install uses cache → faster builds
COPY package.json package-lock.json* ./

RUN npm ci --frozen-lockfile
# npm ci (clean install):
# - Uses exact versions from package-lock.json (reproducible builds)
# - Fails if lock file is out of date (catches developer mistakes)
# - Faster than npm install for CI/CD

# Copy source code and build
COPY . .

RUN npm run build
# Output: dist/ directory with compiled HTML, CSS, JS

# Stage 2 — Serve with Nginx
FROM nginx:alpine AS production

# Copy built files to Nginx's default web root
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx config (for SPA routing fallback)
COPY --from=builder /app/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
