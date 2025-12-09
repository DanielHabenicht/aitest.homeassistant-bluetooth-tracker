ARG BUILD_FROM
FROM $BUILD_FROM

# Install requirements
RUN apk add --no-cache \
    python3 \
    py3-pip \
    bluez \
    bluez-deprecated \
    dbus

# Install Python packages
RUN pip3 install --no-cache-dir \
    bleak \
    flask \
    flask-cors

# Copy application files
COPY rootfs /

# Set working directory
WORKDIR /app

# Make run script executable
RUN chmod a+x /app/run.sh

# Start the application
CMD ["/app/run.sh"]
