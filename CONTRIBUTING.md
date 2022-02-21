# How to contribute code

Pull requests are welcome, but if you're thinking of something
non-trivial, please ask first before investing a lot of work which may
not be accepted.

As of this writing, development is done with Python 3.7, so please
make sure you're using that for your work.  Instructions for setting
up a development environment are given in SETUP.md.  I do all
development on Debian Linux; you can develop on other platforms if you
want, but I'll have zero sympathy for problems that causes.

I'm not a stickler for coding style.  Just try to follow the style
I use.  I suspect at some point in the future, I'll go all-in on
[black](https://pypi.org/project/black/), but not today.

I am a stickler for unit tests.  No code will be accepted without
comprehensive tests.  At a minimum, you should have tests which verify
typical inputs as well as exploring various edge cases like no input
or broken input.  The test suite makes extensive use of unittest.mock
in some places.  I realize this isn't very well known, so please feel
free to ask for help writing these kinds of tests.  All tests must be
written so they run when invoking "./manage.py test" at the top level.

All code gets committed and exercized on the dev branch (which runs on
https://spi-tools-dev.toolforge.org/) before being merged into master
(which runs on https://spi-tools.toolforge.org/).  So, prepare a pull
request against dev.  If there's any merge conflicts, you'll need to
resolve those on your branch before sending the PR.
