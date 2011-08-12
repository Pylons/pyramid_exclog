pyramid_exclog
==============

Overview
--------

A package which logs to a Python :term:`logger` when an exception is raised
by your Pyramid application.

.. warning:: This package currently will not work with any released Pyramid;
   it requires the Pyramid trunk (aka "1.2dev").

Installation
------------

Install using setuptools, e.g. (within a virtualenv)::

  $ easy_install pyramid_exclog

Setup
-----

Once ``pyramid_exclog`` is installed, you must use the ``config.include``
mechanism to include it into your Pyramid project's configuration.  In your
Pyramid project's ``__init__.py``:

.. code-block:: python
   :linenos:

   config = Configurator(.....)
   config.include('pyramid_exclog')

Alternately you can use the ``pyramid.includes`` configuration value in your
``.ini`` file:

.. code-block:: ini
   :linenos:

   [app:myapp]
   pyramid.includes = pyramid_exclog

Using
-----

When this utility is configured into a Pyramid application, whenever a
request to your application causes an exception to be raised, it will log the
exception to a Python :term:`logger`.

By default, the exception logging machinery will log all exceptions (even
those eventually caught by a Pyramid :term:`exception view`) except "http
exceptions" (any exception that derives from the base class
``pyramid.httpexceptions.WSGIHTTPException`` such as ``HTTPFound``).  You can
instruct ``pyramid_exclog`` to ignore custom exception types by using the
``excview.ignore`` configuration setting, described below.

The Python logger name which ``pyramid_exclog`` logs to is named
``exc_logger``.  You can use the logging configuration in your Pyramid
application's ``.ini`` file to change the ``exc_logger`` logger to be of a
specific kind, meaning you can log to a file, to syslog, or to email, and
other locations.  For example, the following configuration sends
``pyramid_exclog`` exception logging info to a file (in the current
directory) named ``exceptions.log``:

.. code-block:: ini
   :linenos:

   # Begin logging configuration

   [loggers]
   keys = root, starter, exc_logger

   [handlers]
   keys = console, exc_handler

   [formatters]
   keys = generic, exc_formatter

   [logger_root]
   level = INFO
   handlers = console

   [logger_starter]
   level = DEBUG
   handlers =
   qualname = starter

   [logger_exc_logger]
   level = ERROR
   handlers = exc_handler
   qualname = exc_logger

   [handler_console]
   class = StreamHandler
   args = (sys.stderr,)
   level = NOTSET
   formatter = generic

   [handler_exc_handler]
   class = FileHandler
   args = ('exception.log',)
   level = ERROR
   formatter = exc_formatter

   [formatter_generic]
   format = %(asctime)s %(levelname)-5.5s [%(name)s][%(threadName)s] %(message)s

   [formatter_exc_formatter]
   format = %(asctime)s %(message)s

   # End logging configuration

Most of the "knobs" you'll need to turn relate to changing the logging
configuration of your application.  For information about the logging file
configuration format, see
http://docs.python.org/release/2.5.2/lib/logging-config-fileformat.html .

However, :mod:`pyramid_exclog`` also has some its own knobs in the form of
configuration settings which are meant to be placed in the application
section of your Pyramid's ``.ini`` file.  These are:

``exclog.ignore``

    A list of dotted Python names representing exception types
    (e.g. ``myapp.MyException``) or builtin exception names (e.g.
    ``NotImplementedError`` or ``KeyError``) that represent exceptions which
    should not ever be logged.  This setting defaults to a list containing
    only ``pyramid.httpexceptions.WSGIHTTPException``.  This list can be in
    the form of a whitespace-separated string, e.g. ``KeyError ValueError
    myapp.MyException`` or it may consume multiple lines in the ``.ini``
    file.

Explicit "Tween" Configuration
------------------------------

Note that the exception logger is implemented as a Pyramid :term:`tween`, and
it can be used in the explicit tween chain if its implicit position in the
tween chain is incorrect (see the output of ``paster ptweens``)::

   [app:myapp]
   pyramid.tweens = someothertween
                    pyramid.tweens.excview_tween_factory
                    pyramid_exclog.exclog_tween_factory

It usually belongs directly above the "MAIN" entry in the ``paster ptweens``
output, and will attempt to sort there by default as the result of having
``include('pyramid_exclog')`` invoked.

Putting it above the ``pyramid.tweens.excview_tween_factory`` will cause it
to log only exceptions that are not caught by an exception view.

More Information
----------------

.. toctree::
   :maxdepth: 1

   api.rst
   glossary.rst


Reporting Bugs / Development Versions
-------------------------------------

Visit http://github.com/Pylons/pyramid_exclog to download development or
tagged versions.

Visit http://github.com/Pylons/pyramid_exclog/issues to report bugs.

Indices and tables
------------------

* :ref:`glossary`
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
