FROM node:20-alpine

EXPOSE 8080

WORKDIR /app

COPY server.js /app

RUN npm install ws

ENV PORT=8080

CMD ["node", "server.js"]
