# Use Node.js 20 (NestJS works great on this)
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files first
COPY package*.json ./

# Install dependencies (including devDependencies for build)
RUN npm install

# Copy the rest of your app
COPY . .

# Build the app using npx
RUN npx nest build

# Expose NestJS default port
EXPOSE 3000

# Run the app
CMD ["npm", "run", "start:prod"]
