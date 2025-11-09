# ---- Build stage ----
FROM node:20-alpine AS build
WORKDIR /app
    
# Copy dependency files first
COPY src/frontend/package*.json ./
RUN npm install
    
# Copy and build app
COPY src/frontend ./
RUN npm run build
    
# ---- Serve stage ----
FROM nginx:alpine
# Copy production build
COPY --from=build /app/build /usr/share/nginx/html
# Copy optional custom nginx config (optional)
# COPY deployment/docker/nginx.conf /etc/nginx/conf.d/default.conf
    
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
