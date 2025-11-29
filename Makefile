.PHONY: up down build logs test shell migrate makemigrations clean

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f api

test:
	docker-compose exec api python manage.py test

shell:
	docker-compose exec api python manage.py shell

migrate:
	docker-compose exec api python manage.py migrate

makemigrations:
	docker-compose exec api python manage.py makemigrations

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

superuser:
	docker-compose exec api python manage.py createsuperuser

collectstatic:
	docker-compose exec api python manage.py collectstatic --noinput
