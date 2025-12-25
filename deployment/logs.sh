#!/bin/bash
# View logs from Docker containers

cd /opt/timeless-love/backend

if [ "$1" == "backend" ]; then
    echo "📝 Backend logs:"
    docker-compose -f docker-compose.production.yml logs -f backend
elif [ "$1" == "nginx" ]; then
    echo "📝 Nginx logs:"
    docker-compose -f docker-compose.production.yml logs -f nginx
else
    echo "📝 All logs:"
    docker-compose -f docker-compose.production.yml logs -f
fi
