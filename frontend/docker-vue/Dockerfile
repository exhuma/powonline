FROM mkenney/npm:7.0-alpine
RUN npm install -g vue-cli && echo "2017-07-09 10:49:26"
ADD docker-entry-point /
RUN chmod +x /docker-entry-point
ENTRYPOINT ["/docker-entry-point"]
