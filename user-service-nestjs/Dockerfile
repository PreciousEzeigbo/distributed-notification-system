# Use Node.js 20 (NestJS works great on this)
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files first
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy the rest of your app
COPY . .

# Build the application
RUN npm run build

# Expose NestJS default port
EXPOSE 3000

# Run in production mode (faster startup)
CMD ["node", "dist/main"]
