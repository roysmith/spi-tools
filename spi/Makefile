all: restart test lint

restart:
	webservice --backend=kubernetes python3.7 restart &

test:
	cd ..; ./manage.py test $(test)

lint:
	cd ..; pylint spi/*.py
