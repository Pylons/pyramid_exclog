1.1 (2022-03-12)
----------------

- Drop support for Python 2.7, 3.5, and 3.6.

- Support Python 3.7, 3.8, 3.9, 3.10.
  See https://github.com/Pylons/pyramid_exclog/pull/35

- Add ``exclog.hide_cookies`` config option to mark certain
  cookie values as hidden from messages.
  See https://github.com/Pylons/pyramid_exclog/pull/39

- Include the license file in the wheel.
  See https://github.com/Pylons/pyramid_exclog/pull/37

- Refactor source repo, blackify, and remove tests from package.
  See https://github.com/Pylons/pyramid_exclog/pull/41

1.0 (2017-04-09)
----------------

- Drop support for Python 3.3.

- Require Pyramid 1.5+.

- Move the tween **over** the ``EXCVIEW`` such that it also handles
  exceptions caused by exception views.
  See https://github.com/Pylons/pyramid_exclog/pull/32

0.8 (2016-09-22)
----------------

- Drop support for Python 2.6 and 3.2.

- Add explicit support for Python 3.4 and 3.5.

- Handle IOError exception when accessing request parameters.

- Fix UnicodeDecodeError on Python 2 when QUERY_STRING is a ``str``
  containing non-ascii bytes.

- Allways pass the logging module text rather than sometimes
  bytes and sometimes text.

0.7 (2013-06-28)
----------------

- Add explicit support for Python 3.3.

- Do not error if the URL, query string or post data contains unexpected
  encodings.

- Try to log an exception when logging fails:  often the middleware is used
  just inside one which converts all errors into ServerErrors (500), hiding
  any exceptions triggered while logging.

- Add ``unauthenticated_user()`` to the output when the ``extra_info`` key
  is set to True (PR #11).

- Add a hook for constructing custom log messages (PR #15).

- Changed testing regime to allow ``setup.py dev``.

- We no longer test under Python 2.5 (although it's not explicitly broken
  under 2.5).

0.6 (2012-03-24)
----------------

- Add an ``exclog.extra_info`` setting to the exclog configuration.  If it's
  true, send WSGI environment and params info in the log message.

0.5 (2011-09-27)
----------------

- Python 3.2 compatibility under Pyramid 1.3.X.

0.4 (2011-08-24)
-----------------

- Docs-only changes.

0.3 (2011-08-21)
----------------

- Don't register an implicit tween factory with an alias (compat with future
  1.2).

0.2 (2011-08-13)
----------------

- Improve documentation by providing examples of logging to file, email and
  by describing deltas to default Pyramid 1.2 logging config.

- Use string value as factory to add_tween in includeme.

0.1 (2011-08-11)
----------------

- Initial release.
