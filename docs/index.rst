==============
pyramid_exclog
==============

Overview
========

A package which logs Pyramid application exception (error) information to a
standard Python :term:`logger`.  This add-on is most useful when used in
production applications, because the logger can be configured to log to a
file, to UNIX syslog, to the Windows Event Log, or even to email.

.. warning:: This package will only work with Pyramid 1.5 and better.

Installation
============

Stable release
--------------

To install pyramid_exclog, run this command in your terminal:

.. code-block:: console

    $ pip install pyramid_exclog

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: https://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for pyramid_exclog can be downloaded from the `Github repo`_.

.. code-block:: console

    $ git clone https://github.com/Pylons/pyramid_exclog.git

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ pip install -e .

.. _Github repo: https://github.com/Pylons/pyramid_exclog

Setup
=====

Once ``pyramid_exclog`` is installed, you must use the ``config.include``
mechanism to include it into your Pyramid project's configuration.  In your
Pyramid project's ``__init__.py``:

.. code-block:: python
   :linenos:

   config = Configurator(...)
   config.include('pyramid_exclog')

Alternately you can use the ``pyramid.includes`` configuration value in your
``.ini`` file:

.. code-block:: ini
   :linenos:

   [app:myapp]
   pyramid.includes = pyramid_exclog

Using
=====

When this add-on is included into your Pyramid application, whenever a
request to your application causes an exception to be raised, the add-on will
send the URL that caused the exception, the exception type, and its related
traceback information to a standard Python :term:`logger` named
``exc_logger``.

You can use the logging configuration in your Pyramid application's ``.ini``
file to add a logger named ``exc_logger``.  This logger should be hooked up a
particular logging handler, which will allow you to use the standard Python
logging machinery to send your exceptions to a file, to syslog, or to an
email address.

It's not generally useful to add exception logger configuration to a
``development.ini`` file, because typically exceptions are displayed in the
interactive debugger and to the console which started the application, and
you really don't care much about actually *logging* the exception
information.  However, it's very appropriate to add exception logger
configuration to a ``production.ini`` file.

The following logging configuration statements are in the *default*
``production.ini`` file generated by all Pyramid scaffolding:

.. code-block:: ini
   :linenos:

   # Begin logging configuration

   [loggers]
   keys = root, myapp

   [handlers]
   keys = console

   [formatters]
   keys = generic

   [logger_root]
   level = WARN
   handlers = console

   [logger_myapp]
   level = WARN
   handlers =
   qualname = myapp

   [handler_console]
   class = StreamHandler
   args = (sys.stderr,)
   level = NOTSET
   formatter = generic

   [formatter_generic]
   format = %(asctime)s %(levelname)-5.5s [%(name)s][%(threadName)s] %(message)s

   # End logging configuration

The standard logging configuration of the ``production.ini`` of a scaffolded
Pyramid application does not name a logger named ``exc_logger``.  Therefore,
to start making use of ``pyramid_exclog``, you'll have to add an
``exc_logger`` logger to the configuration.  To do so:

1) Append ``, exc_logger`` to the ``keys`` value of the ``[loggers]`` section,

2) Append ``, exc_handler`` to the ``keys`` value of the ``[handlers]``
   section.

3) Append ``, exc_formatter`` to the ``keys`` value of the ``[formatters]``
   section.

4) Add a section named ``[logger_exc_logger]`` with logger information
   related to the new exception logger.

5) Add a section named ``[handler_exc_handler]`` with handler information
   related to the new exception logger.  In our example, it will have
   configuration that tells it to log to a file in the same directory as the
   ``.ini`` file named ``exceptions.log``.

6) Add a section named ``[formatter_exc_formatter]`` with message formatting
   information related to the messages sent to the ``exc_handler`` handler.
   By default we'll send only the time and the message.

The resulting configuration will look like this:

.. code-block:: ini
   :linenos:

   # Begin logging configuration

   [loggers]
   keys = root, myapp, exc_logger

   [handlers]
   keys = console, exc_handler

   [formatters]
   keys = generic, exc_formatter

   [logger_root]
   level = WARN
   handlers = console

   [logger_myapp]
   level = WARN
   handlers =
   qualname = myapp

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
   args = ('%(here)s/exceptions.log',)
   level = ERROR
   formatter = exc_formatter

   [formatter_generic]
   format = %(asctime)s %(levelname)-5.5s [%(name)s][%(threadName)s] %(message)s

   [formatter_exc_formatter]
   format = %(asctime)s %(message)s

   # End logging configuration

Once you've changed your logging configuration as per the above, and you
restart your Pyramid application, all exceptions will be logged to a file
named ``exceptions.log`` in the directory that the ``production.ini`` file
lives.

You can get fancier with logging as necessary by familiarizing yourself with
the Python ``logging`` module configuration format.  For example, here's an
alternate configuration that logs exceptions via email to a user named
``from@example.com`` to a user named ``to@example.com`` via the SMTP server
on the local host at port 25; each email will have the subject ``myapp
Exception``:

.. code-block:: ini
   :linenos:

   # Begin logging configuration

   [loggers]
   keys = root, myapp, exc_logger

   [handlers]
   keys = console, exc_handler

   [formatters]
   keys = generic, exc_formatter

   [logger_root]
   level = WARN
   handlers = console

   [logger_myapp]
   level = WARN
   handlers =
   qualname = myapp

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
   class = handlers.SMTPHandler
   args = (('localhost', 25), 'from@example.com', ['to@example.com'], 'myapp Exception')
   level = ERROR
   formatter = exc_formatter

   [formatter_generic]
   format = %(asctime)s %(levelname)-5.5s [%(name)s][%(threadName)s] %(message)s

   [formatter_exc_formatter]
   format = %(asctime)s %(message)s

   # End logging configuration

When the above configuration is used, exceptions will be sent via email
instead of sent to a file.

For information about logging in general see the `Pythong logging module
documentation <https://docs.python.org/library/logging.html>`_.  Practical
tips are contained within the `Python logging cookbook
<https://docs.python.org/howto/logging-cookbook.html#logging-cookbook>`_.
More information about the the ``.ini`` logging file configuration format is
at
https://docs.python.org/library/logging.config.html#configuration-file-format
.

Settings
=========

:mod:`pyramid_exclog`` also has some its own settings in the form of
configuration values which are meant to be placed in the ``[app:myapp]``
section of your Pyramid's ``.ini`` file.  These are:

``exclog.ignore``

   By default, the exception logging machinery will log all exceptions (even
   those eventually caught by a Pyramid :term:`exception view`) except "http
   exceptions" (any exception that derives from the base class
   ``pyramid.httpexceptions.WSGIHTTPException`` such as ``HTTPFound``).  You
   can instruct ``pyramid_exclog`` to override this default in order to
   ignore custom exception types (or to re-enable logging "http exceptions")
   by using the ``excview.ignore`` configuration setting.

   ``excview.ignore`` is a list of dotted Python names representing exception
   types (e.g. ``myapp.MyException``) or builtin exception names (e.g.
   ``NotImplementedError`` or ``KeyError``) that represent exceptions which
   should never be logged.  This list can be in the form of a
   whitespace-separated string, e.g. ``KeyError ValueError
   myapp.MyException`` or it may consume multiple lines in the ``.ini`` file.

   This setting defaults to a list containing only
   ``pyramid.httpexceptions.WSGIHTTPException``.

   An example:

   .. code-block:: ini

      [app:myapp]
      exclog.ignore = pyramid.httpexceptions.WSGIHTTPException
                      KeyError
                      myapp.exceptions.MyException

``exclog.extra_info``

   By default the only content in error messages is the URL that was
   accessed (retrieved from the url attribute of ``pyramid.request.Request``)
   and the exception information that is appended by Python's
   ``Logger.exception`` function.

   If ``exclog.extra_info`` is true the error message will also include
   the environ and params attributes of ``pyramid.request.Request`` formatted
   using ``pprint.pformat()``. The output from
   ``pyramid.security.unauthenticated_id()`` is also included.

   This setting defaults to false

   An example:

   .. code-block:: ini

      [app:myapp]
      exclog.extra_info = true

``exclog.get_message``

   If a customized error message is needed, the ``exclog.get_message``
   setting can be pointed at a function that takes a request as its only
   argument and returns a string. It can be either a dotted name or the
   actual function. For example:

   .. code-block:: ini

      [app:myapp]
      exclog.get_message = myapp.somemodule.get_exc_log_message

   If ``exclog.get_message`` is set, ``exclog.extra_info`` will be ignored.

``exclog.hidden_cookies``

   A list of keys of cookies to hide in the error message.  The cookie's value
   will be replaced with "hidden", so you can still tell whether the cookie was
   present.

   This works with either ``exclog.extra_info`` or ``exclog.get_message``.  If
   ``exclog.hidden_cookies`` is set, then any function specified in
   ``exclog.get_message`` will receive a copy of the request with the cookies
   already replaced.

   An example:

   .. code-block:: ini

      [app:myapp]
      exclog.hidden_cookies = auth_tkt
                              another_cookie

Explicit "Tween" Configuration
==============================

Note that the exception logger is implemented as a Pyramid :term:`tween`, and
it can be used in the explicit tween chain if its implicit position in the
tween chain is incorrect (see the output of ``ptweens``)::

   [app:myapp]
   pyramid.tweens = someothertween
                    pyramid_exclog.exclog_tween_factory
                    pyramid.tweens.excview_tween_factory

It usually belongs directly above the ``pyramid.tweens.excview_tween_factory``
entry in the ``ptweens`` output, and will attempt to sort there by default as
the result of having ``config.include('pyramid_exclog')`` invoked.

Deployment under mod_wsgi
=========================

To make logging facilities available when loading an application via
mod_wsgi, like it behaves with pserve, you must call the ``logging.fileConfig``
function on the ini file containing the logger entry.

Here's an example of a ``run.wsgi`` file:

.. code-block:: python

    import os
    from pyramid.paster import get_app, setup_logging

    here = os.path.dirname(os.path.abspath(__file__))
    conf = os.path.join(here, 'production.ini')
    setup_logging(conf)

    application = get_app(conf, 'main')

More Information
================

.. toctree::
   :maxdepth: 1

   api.rst
   glossary.rst


Reporting Bugs / Development Versions
=====================================

Visit https://github.com/Pylons/pyramid_exclog to download development or
tagged versions.

Visit https://github.com/Pylons/pyramid_exclog/issues to report bugs.

Indices and tables
------------------

* :ref:`glossary`
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
