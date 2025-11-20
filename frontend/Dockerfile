FROM node:20-bullseye-slim

ARG VITE_API_URL=http://backend:8000
ENV VITE_API_URL=${VITE_API_URL}

WORKDIR /app

# Install dependencies inside the container to ensure native optional deps
# are resolved for the container architecture.
COPY frontend/package.json frontend/package-lock.json* ./
# Install dependencies including optional native modules. Some optional
# packages (like Rollup native binaries) are required by the build step and
# must be installed for the image's architecture. If this fails on your
# platform, build the frontend locally and place `dist/` in the build context
# so the image can reuse it.
RUN npm ci

# Copy the rest of the frontend source after installing deps to avoid
# overwriting node_modules with host artifacts.
COPY frontend/ /app/

EXPOSE 3000
# If a prebuilt `dist` exists in the build context (e.g. built on the host),
# use it. Otherwise run the build inside the image. Building inside some
# container/arch combinations can fail due to optional native deps, so the
# recommended flow is to build locally and let the image reuse that `dist`.
RUN if [ -d /app/dist ]; then echo "Using prebuilt /app/dist"; else npm run build; fi
RUN npm install -g serve
CMD ["serve", "-s", "dist", "-l", "3000"]
