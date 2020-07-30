all: test lint

test:
	cd ..; ./manage.py test $(test)

lint:
	cd ..; pylint spi/*.py
