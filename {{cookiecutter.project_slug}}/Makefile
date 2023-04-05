.PHONY: help lock twine lint test format up_db wait_for_db run_locally run clean preprod_release


.DEFAULT: help
help:
	@echo "Usage: make <command>"
	@echo
	@echo "Commands:"
	@echo "make venv"
	@echo "		Install virtual environment"
	@echo "make pyenv"
	@echo "		Install pyenv and virtual environment"
	@echo "lock	Lock dev virtual environment"
	@echo "twine	Publish package to the Company PYPI"
	@echo "test	Test Project"
	@echo "test_locally	Test Project locally"
	@echo "format	Run all pre-commit hooks"
	@echo "up_db	Build and up database container."
	@echo "wait_for_db	Wait whyle DB is starting up."
	@echo "run	Build and run server container."
	@echo "run_server	Run server locally."
	@echo "run_periodic	Run periodic tasks locally."
	@echo "clean	Down containers, remove volumes and intermediate containers."
	@echo "preprod_release	Increments tag number and pushes tagged HEAD to dev and preprod."


venv:
	@echo "Install virtual environment"
	@echo "Usage: make venv"
	{ \
	pip install pipenv; \
	ls | grep Pipfile.lock && pipenv sync -d || pipenv update -d; \
	}


pyenv:
	@echo "Install pyenv and virtual environment"
	@echo "Usage: make pyenv"
	{ \
	ls -la ~/ | grep .pyenv && echo Pyenv already installed || ((curl https://pyenv.run | bash) && exec $SHELL); \
	venv=$$(cat .python-version | tr -d '\n'); \
	python_version=$$(echo $$venv | rev | cut -d'-' -f 1 | rev); \
	~/.pyenv/bin/pyenv versions | grep $$python_version && echo Python $$python_version already exists || (~/.pyenv/bin/pyenv update && ~/.pyenv/bin/pyenv install $$python_version); \
	~/.pyenv/bin/pyenv versions | grep $$venv && echo Venv $$venv already exists || (~/.pyenv/bin/pyenv virtualenv $$python_version $$venv); \
	. ~/.pyenv/versions/$$venv/bin/activate; \
	pip install pipenv; \
	ls | grep Pipfile.lock && pipenv sync -d || pipenv update -d; \
	}

lock:
	@echo "Lock dev virtual environment"
	@echo "Usage: make lock"
	{ \
    pipenv lock; \
    chown $$UID:$$GID Pipfile.lock; \
	}

twine:
	@echo "Publish package to the Company PYPI"
	@echo "Usage: make twine"
	{ \
    python -m build; \
    twine upload -r nexus dist/*.tar.gz --config-file .pypirc; \
    rm dist/*; \
}

test:
	@echo "Test Project"
	@echo "Usage: make test"
	{ \
  	pytest --dead-fixtures; \
  	pytest -vv --pdb; \
  	rm .coverage; \
	}

format:
	@echo "Run all pre-commit hooks"
	@echo "Usage: make format"
	pre-commit run --all-files

up_db:
	@echo "Build and up database container."
	@docker compose up --build --remove-orphans -d register-database
	@echo "Type 'CTRL C' to shut down DB and 'make clean' to down containers, "
	@echo "remove volumes and intermediate containers."
	@make wait_for_db
	alembic upgrade head
	docker attach register-database

wait_for_db:
	@echo "Wait whyle DB is starting up."
	@until docker container exec -it register-database pg_isready; \
	do \
		>&2 echo "waiting for Postgres..."; \
		sleep 5; \
	done
	@echo "database has started"

up_containers:
	@echo "Build, up database and server containers."
	@docker compose up --build --remove-orphans -d register-database
	@make wait_for_db
	@docker compose up --build --remove-orphans register

run_server:
	@echo "Run server locally."
	@make wait_for_db
	@export DB_HOST=127.0.0.1; uvicorn app.main:app --reload

run_app:
	@echo "Build, up database container and run server locally."
	@docker compose up --build --remove-orphans -d register-database
	@make run_server

run_periodic:
	@echo "Run periodic tasks locally."
	python ./app/main.py --periodic_tasks

clean:
	@echo "Down containers, remove volumes and intermediate containers."
	@docker compose down --volumes --remove-orphans

test_locally:
	echo "Test Project locally";\
	echo "Usage: make test_locally";\
	export DB_HOST=127.0.0.1;\
	make test

preprod_release:
	@echo "Increments tag number and pushes tagged HEAD to dev and preprod."
	@bash ./release_to_preprod.sh
