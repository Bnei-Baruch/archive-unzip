ARG backend_url="https://kabbalahmedia.info/assets/api/"

FROM node:latest AS build

LABEL maintainer="edoshor@gmail.com"

ARG backend_url

WORKDIR /app

ENV REACT_APP_BACKEND=${backend_url}

COPY . .

RUN yarn install --immutable && \
    yarn build && \
    rm -rf node_modules

FROM alpine
COPY --from=build /app/build /app
COPY misc/docker-entrypoint.sh .
ENTRYPOINT ["/docker-entrypoint.sh"]
