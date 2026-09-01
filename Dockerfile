# Multistage Dockerfile for S.P.O.T. React PWA Frontend
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency definitions
COPY package*.json ./
RUN npm ci

# Copy application source code
COPY . .

# Build production React PWA bundle
RUN npm run build

# Stage 2: Serve with Nginx for low-latency PWA delivery
FROM nginx:alpine

# Copy built dist assets into Nginx web root
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose HTTP port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
