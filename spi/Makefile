all: lint

test:
	cd ..; ./manage.py test $(test)

lint:	test
	cd ..; pylint spi/*.py
