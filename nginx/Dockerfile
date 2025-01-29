FROM nginx:alpine

# Remove the default Nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy the Nginx configuration template
COPY default.conf /etc/nginx/templates/default.conf.template

# Use envsubst to replace placeholders with environment variables
CMD ["/bin/sh", "-c", "envsubst '${DOMAIN_NAME}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
