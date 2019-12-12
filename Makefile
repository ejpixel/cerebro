SHELL=/bin/bash

.PHONY: setup, run

setup:
	- virtualenv venv -p python3.6
	- source venv/bin/activate && \
		pip install -r requirements.txt

run-as-dev:
	- export FLASK_ENV=development && \
		FLASK_APP=app.py && \
		source venv/bin/activate && \
		flask run

run:
	- export FLASK_APP=app.py && \
		source venv/bin/activate && \
		flask run

deploy:
	- git push heroku master
