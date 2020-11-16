---------------------------------
Getting everything up and running
---------------------------------

1. Rename .env.example to .env

2. Add your email and Stripe credentials to your .env file.
  (use your instance/settings.py file from section 20's code as a reference)

3. Open a terminal configured to run Docker and then run:

docker-compose down -v
docker-compose up --build
docker-compose exec web turboquant db reset --with-testdb
docker-compose exec web turboquant add all
docker-compose exec web turboquant flake8
docker-compose exec web turboquant test
