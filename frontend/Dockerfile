# Dockerfile for the frontend
FROM node:14-alpine

WORKDIR /app

COPY package*.json ./
RUN yarn install

COPY . ./

ENV SI_CLOUD_ENV production

# RUN yarn build

EXPOSE 3000

CMD ["yarn", "start"]
