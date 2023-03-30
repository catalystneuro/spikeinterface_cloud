# Dockerfile for the frontend
FROM node:14-alpine

WORKDIR /app

COPY frontend/package*.json ./
RUN yarn install

COPY frontend ./

# RUN yarn build

EXPOSE 3000

CMD ["yarn", "start"]
