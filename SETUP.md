# To setup a working dev environment:

(this may still be incomplete)

- Make sure you have Python 3.7 installed.  In theory, this should work with anything newer than 3.7, but it's never been tested.
- Make a directory where you're going to work, which we'll call $dir
  - If you are going to run a webserver, you need to follow the directory layout [described on wikitech](https://wikitech.wikimedia.org/wiki/Help:Toolforge/Web/Python)
  - If you are just going to run unit tests, $dir can be anywhere
- cd $dir
- git clone git@github.com:roysmith/spi-tools.git src
  - Alternatively: git clone https://github.com/roysmith/spi-tools.git src
  - And probably several other variations
- python3 -m venv venv
- source venv/bin/activate
- pip install --upgrade pip
  - This step is optional, but it's a good idea to make sure pip is up to date.
- pip install -r src/requirements.txt
  - This will take a few minutes.

# To run unit tests outside of Toolforge

- SPI_TOOLS_CONGIG_FILE=$dir/src/unsafe-sample-config.ini
- export SPI_TOOLS_CONGIG_FILE
- cd $dir/src
- ./manage.py test
