PIPENV_RUN := pipenv run
PG_DOCKERFILE_NAME := fastapi-users-test-mongo

test_all: test_pg test_mysql test_sqlite

test_pg: export DATABASE_URL=postgresql://username:password@localhost:5432/testsuite
test_pg:
	docker-compose -f scripts/docker-compose.yml up -d postgres
	bash scripts/test.sh -svv
	docker-compose stop postgres

test_mysql: export DATABASE_URL=mysql://username:password@127.0.0.1:3306/testsuite
test_mysql:
	docker-compose -f "scripts/docker-compose.yml" up -d mysql
	bash scripts/test.sh -svv
	docker-compose stop mysql

test_sqlite:
	bash scripts/test.sh -svv