``pyramid_exclog``
===================

A package which logs Pyramid application exception (error) information to a
standard Python logger.  This add-on is most useful when used in production
applications, because the logger can be configured to log to a file, to UNIX
syslog, to the Windows Event Log, or even to email.

See the documentation at
https://docs.pylonsproject.org/projects/pyramid_exclog/dev/ for more
information.

This package currently will not work with any released Pyramid; it requires
the Pyramid trunk (aka "1.2dev"), available from
https://github.com/Pylons/pyramid .
