FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json* tsconfig.json ./
RUN npm install --production=false

COPY src ./src

RUN npm run build

ENV NODE_ENV=production
EXPOSE 4000

CMD ["node", "dist/index.js"]

