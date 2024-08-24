# gunicorn_config.py

bind = "0.0.0.0:8000"
module = "project.wsgi:application"

workers = 2  # Adjust based on your server's resources
worker_connections = 1000
threads = 2

#certfile = "/etc/letsencrypt/live/raspberrypi/fullchain.pem"
#keyfile = "/etc/letsencrypt/live/raspberrypi/privkey.pem"