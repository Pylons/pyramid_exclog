from pyramid import testing
import sys
import unittest


class Test_exclog_tween_factory(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.registry = self.config.registry

    def _callFUT(self):
        from pyramid_exclog import exclog_tween_factory

        return exclog_tween_factory(None, self.registry)

    def test_no_recipients(self):
        handler = self._callFUT()
        self.assertEqual(handler.__name__, 'exclog_tween')


class Test_exclog_tween(unittest.TestCase):
    def setUp(self):
        self.request = request = _request_factory('/')
        self.config = testing.setUp(request=request)
        self.registry = self.config.registry
        self.registry.settings = {}
        request.registry = self.registry
        self.logger = DummyLogger()

    def getLogger(self, name):
        self.logger.name = name
        return self.logger

    def handler(self, request):
        raise NotImplementedError

    def _callFUT(
        self, handler=None, registry=None, request=None, getLogger=None
    ):
        from pyramid_exclog import exclog_tween_factory

        if handler is None:
            handler = self.handler
        if registry is None:
            registry = self.registry
        if request is None:
            request = self.request
        if getLogger is None:
            getLogger = self.getLogger
            registry.settings['exclog.getLogger'] = getLogger
        tween = exclog_tween_factory(handler, registry)
        return tween(request)

    def test_ignored(self):
        self.registry.settings['exclog.ignore'] = (NotImplementedError,)
        self.assertRaises(NotImplementedError, self._callFUT)
        self.assertEqual(len(self.logger.exceptions), 0)

    def test_notignored(self):
        self.assertRaises(NotImplementedError, self._callFUT)
        self.assertEqual(len(self.logger.exceptions), 1)
        msg = self.logger.exceptions[0]
        self.assertEqual(msg, repr(self.request.url))

    def test_exc_info(self):
        def handler(request):
            try:
                raise NotImplementedError
            except Exception as ex:
                exc_info = sys.exc_info()
                try:
                    request.exception = ex
                    request.exc_info = exc_info
                finally:
                    del exc_info
            return b'dummy response'

        result = self._callFUT(handler=handler)
        self.assertEqual(b'dummy response', result)
        self.assertEqual(len(self.logger.exceptions), 1)
        msg = self.logger.exceptions[0]
        self.assertEqual(msg, repr(self.request.url))

    def test_extra_info(self):
        self.registry.settings['exclog.extra_info'] = True
        self.assertRaises(NotImplementedError, self._callFUT)
        self.assertEqual(len(self.logger.exceptions), 1)
        msg = self.logger.exceptions[0].strip()
        self.assertTrue(
            msg.startswith("'http://localhost/'\n\nENVIRONMENT"), msg
        )
        self.assertTrue("PARAMETERS\n\nNestedMultiDict([])" in msg)
        self.assertTrue('ENVIRONMENT' in msg)

    def test_get_message(self):
        self.registry.settings['exclog.get_message'] = lambda req: 'MESSAGE'
        self.assertRaises(NotImplementedError, self._callFUT)
        self.assertEqual(len(self.logger.exceptions), 1)
        msg = self.logger.exceptions[0]
        self.assertEqual(msg, 'MESSAGE')

    def test_hidden_cookies(self):
        self.registry.settings['exclog.extra_info'] = True
        self.registry.settings['exclog.hidden_cookies'] = ['test_cookie']
        self.request.cookies['test_cookie'] = 'test_cookie_value'
        self.assertRaises(NotImplementedError, self._callFUT)
        msg = self.logger.exceptions[0]
        self.assertTrue('test_cookie=hidden' in msg, msg)
        self.assertFalse('test_cookie_value' in msg)

    def test_user_info_user(self):
        self.config.testing_securitypolicy(userid='hank', permissive=True)
        self.registry.settings['exclog.extra_info'] = True
        self.assertRaises(NotImplementedError, self._callFUT)
        self.assertEqual(len(self.logger.exceptions), 1)
        msg = self.logger.exceptions[0]
        self.assertTrue('UNAUTHENTICATED USER\n\nhank' in msg, msg)

    def test_user_info_no_user(self):
        self.registry.settings['exclog.extra_info'] = True
        self.assertRaises(NotImplementedError, self._callFUT)
        self.assertEqual(len(self.logger.exceptions), 1)
        msg = self.logger.exceptions[0]
        self.assertTrue('UNAUTHENTICATED USER\n\nNone\n' in msg, msg)

    def test_exception_while_logging(self):
        from pyramid.request import Request

        bang = AssertionError('bang')

        class BadRequest(Request):
            @property
            def url(self):
                raise bang

        request = _request_factory('/', request_class=BadRequest)
        self.assertRaises(Exception, self._callFUT, request=request)
        msg = self.logger.exceptions[0]
        self.assertEqual('Exception while logging', msg)
        raised = self.logger.exc_info[0][1]
        self.assertEqual(raised, bang)


class Test__get_url(unittest.TestCase):
    def _callFUT(self, request):
        from pyramid_exclog import _get_url

        return _get_url(request)

    def test_normal(self):
        from pyramid.testing import DummyRequest

        request = DummyRequest()
        self.assertEqual(self._callFUT(request), "'http://example.com'")

    def test_w_deocode_error_wo_qs(self):
        request = _request_factory('/')
        request.environ['SCRIPT_NAME'] = '/script'
        request.environ['PATH_INFO'] = '/path/with/latin1/\x80'
        self.assertEqual(
            self._callFUT(request),
            r"could not decode url: 'http://localhost/script/path/with/latin1/\x80'",
        )

    def test_w_deocode_error_w_qs(self):
        request = _request_factory('/')
        request.environ['SCRIPT_NAME'] = '/script'
        request.environ['PATH_INFO'] = '/path/with/latin1/\x80'
        request.environ['QUERY_STRING'] = 'foo=bar'
        self.assertEqual(
            self._callFUT(request),
            r"could not decode url: 'http://localhost/script/path/with/latin1/\x80"
            r"?foo=bar'",
        )


class Test__get_message(unittest.TestCase):
    def _callFUT(self, request):
        from pyramid_exclog import _get_message

        return _get_message(request)

    def test_evil_encodings(self):
        request = _request_factory('/%FA')  # not utf-8
        msg = self._callFUT(request)
        self.assertTrue("could not decode url: 'http://localhost/" in msg)

    def test_return_type_is_unicode(self):
        # _get_message should return something the logging module accepts.
        # this, apparently is unicode or ascii-encoded bytes. Unfortunately,
        # unicode fails with some handlers if you do not set the encoding
        # on them.
        request = _request_factory('/url')  # not utf-8
        msg = self._callFUT(request)
        self.assertTrue(isinstance(msg, str), repr(msg))

    def test_evil_encodings_extra_info(self):
        request = _request_factory('/url?%FA=%FA')  # not utf-8
        msg = self._callFUT(request)
        self.assertTrue("could not decode params" in msg, msg)

    def test_unicode_user_id_with_non_utf_8_url(self):
        # On Python 2 we may get a unicode userid while QUERY_STRING is a "str"
        # object containing non-ascii bytes.
        with testing.testConfig() as config:
            config.testing_securitypolicy(
                userid=b'\xe6\xbc\xa2'.decode('utf-8')
            )
            request = _request_factory('/')
            request.environ['PATH_INFO'] = '/url'
            request.environ['QUERY_STRING'] = '\xfa=\xfa'
            msg = self._callFUT(request)
        self.assertTrue("could not decode params" in msg, msg)

    def test_non_ascii_bytes_in_userid(self):
        byte_str = b'\xe6\xbc\xa2'
        with testing.testConfig() as config:
            config.testing_securitypolicy(userid=byte_str)
            request = _request_factory('/')
            msg = self._callFUT(request)
        self.assertTrue(repr(byte_str) in msg, msg)

    def test_integer_user_id(self):
        # userids can apparently be integers as well
        with testing.testConfig() as config:
            config.testing_securitypolicy(userid=42)
            request = _request_factory('/')
            msg = self._callFUT(request)
        self.assertTrue('42' in msg)

    def test_evil_encodings_extra_info_POST(self):
        request = _request_factory(
            '/url',
            content_type='application/x-www-form-urlencoded; charset=utf-8',
            POST='%FA=%FA',
        )  # not utf-8
        self._callFUT(request)  # doesn't fail

    def test_io_error(self):
        from pyramid.request import Request

        bang = IOError('bang')

        class BadRequest(Request):
            @property
            def params(self):
                raise bang

        request = _request_factory('/', request_class=BadRequest)
        msg = self._callFUT(request)
        self.assertTrue("IOError while decoding params: bang" in msg, msg)


class Test_includeme(unittest.TestCase):
    def _callFUT(self, config):
        from pyramid_exclog import includeme

        return includeme(config)

    def test_it(self):
        from pyramid.httpexceptions import WSGIHTTPException
        from pyramid.tweens import EXCVIEW

        config = DummyConfig()
        self._callFUT(config)
        self.assertEqual(
            config.tweens,
            [
                (
                    'pyramid_exclog.exclog_tween_factory',
                    None,
                    [EXCVIEW, 'pyramid_tm.tm_tween_factory'],
                )
            ],
        )
        self.assertEqual(
            config.registry.settings['exclog.ignore'], (WSGIHTTPException,)
        )

    def test_it_withignored_builtin(self):
        config = DummyConfig()
        config.settings['exclog.ignore'] = 'NotImplementedError'
        self._callFUT(config)
        self.assertEqual(
            config.registry.settings['exclog.ignore'], (NotImplementedError,)
        )

    def test_it_withignored_nonbuiltin(self):
        config = DummyConfig()
        config.settings['exclog.ignore'] = 'tests.test_it.DummyException'
        self._callFUT(config)
        self.assertEqual(
            config.registry.settings['exclog.ignore'], (DummyException,)
        )

    def test_it_with_extra_info(self):
        config = DummyConfig()
        config.settings['exclog.extra_info'] = 'true'
        self._callFUT(config)
        self.assertEqual(config.registry.settings['exclog.extra_info'], True)

    def test_it_with_get_message(self):
        config = DummyConfig()
        get_message = lambda req: 'MESSAGE'  # noqa E722
        config.settings['exclog.get_message'] = get_message
        self._callFUT(config)
        self.assertEqual(
            config.registry.settings['exclog.get_message'], get_message
        )

    def test_get_message_not_set_by_includeme(self):
        config = DummyConfig()
        self._callFUT(config)
        self.assertTrue('exclog.get_message' not in config.registry.settings)


class DummyException(object):
    pass


class DummyLogger(object):
    def __init__(self):
        self.exceptions = []
        self.exc_info = []

    def error(self, msg, exc_info=None):
        self.exceptions.append(msg)
        self.exc_info.append(exc_info)

    def exception(self, msg):
        self.exceptions.append(msg)
        self.exc_info.append(sys.exc_info())


class DummyConfig(object):
    def __init__(self):
        self.tweens = []
        self.registry = self
        self.settings = {}

    def add_tween(self, factory, under=None, over=None):
        self.tweens.append((factory, under, over))

    def maybe_dotted(self, obj):
        """NOTE: ``obj`` should NOT be a dotted name."""
        return obj


def _request_factory(*args, **kwargs):
    """Construct a request object for testing

    This will pass on any args and kwargs to the specified class instance.

    :param request_class: Specific class to use to create the request object
    :return: An instantiated version of the request class for testing
    """
    from pyramid.request import Request
    from pyramid.threadlocal import get_current_registry

    request = kwargs.pop("request_class", Request).blank(*args, **kwargs)

    # Pyramid 2.0 does not appear to attach a registry by default which will
    # lead to crashes we aren't looking for.
    request.registry = get_current_registry()

    return request
