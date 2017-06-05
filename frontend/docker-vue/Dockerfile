FROM mkenney/npm:7.0-alpine
RUN npm install -g vue-cli
ADD docker-entry-point /
RUN chmod +x /docker-entry-point
ENTRYPOINT ["/docker-entry-point"]
