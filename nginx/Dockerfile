textFROM nginx:alpine

# Copy Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create log directory
RUN mkdir -p /var/log/nginx && \
    chown -R nginx:nginx /var/log/nginx

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -q -O- http://localhost/health || exit 1

# Run Nginx
CMD ["nginx", "-g", "daemon off;"]