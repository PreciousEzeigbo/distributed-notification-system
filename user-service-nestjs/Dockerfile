# Use Node.js 20 (NestJS works great on this)
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files first
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of your app
COPY . .

# Expose NestJS default port
EXPOSE 3000

# Run in development mode (will be overridden by docker-compose command)
CMD ["npm", "run", "start:dev"]
