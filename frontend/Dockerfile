# Dockerfile for the frontend
FROM node:19.2-bullseye-slim

WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install

COPY . ./

# RUN yarn build

EXPOSE 5173

CMD ["npm", "run", "start"]