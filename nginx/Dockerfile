FROM nginx:alpine

RUN rm -f /etc/nginx/conf.d/default.conf
COPY default.conf /etc/nginx/templates/default.conf.template

CMD ["/bin/sh", "-c", "envsubst '${DOMAIN_NAME}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && exec nginx -g 'daemon off;'"]
