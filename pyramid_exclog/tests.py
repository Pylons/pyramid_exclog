import sys
import unittest
from pyramid import testing

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
        from pyramid.request import Request
        request = Request.blank('/')
        self.request = request
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

    def _callFUT(self, handler=None, registry=None, request=None,
                 getLogger=None):
        from pyramid_exclog import exclog_tween_factory
        if handler is None:
            handler = self.handler
        if registry is None:
            registry = self.registry
        if request is None:
            request = self.request
        if getLogger is None:
            getLogger = self.getLogger
        tween = exclog_tween_factory(handler, registry)
        return tween(request, getLogger=getLogger)

    def test_ignored(self):
        self.registry.settings['exclog.ignore'] = (NotImplementedError,)
        self.assertRaises(NotImplementedError, self._callFUT)
        self.assertEqual(len(self.logger.exceptions), 0)

    def test_notignored(self):
        self.assertRaises(NotImplementedError, self._callFUT)
        self.assertEqual(len(self.logger.exceptions), 1)
        msg = self.logger.exceptions[0]
        self.assertEqual(msg, self.request.url)

    def test_extra_info(self):
        self.registry.settings['exclog.extra_info'] = True
        self.assertRaises(NotImplementedError, self._callFUT)
        self.assertEqual(len(self.logger.exceptions), 1)
        msg = self.logger.exceptions[0].strip()
        self.assertTrue(msg.startswith("http://localhost/\n\nENVIRONMENT"))
        self.assertTrue("PARAMETERS\n\nNestedMultiDict([])" in msg)
        self.assertTrue('ENVIRONMENT' in msg)

    def test_get_message(self):
        self.registry.settings['exclog.get_message'] = lambda req: 'MESSAGE'
        self.assertRaises(NotImplementedError, self._callFUT)
        self.assertEqual(len(self.logger.exceptions), 1)
        msg = self.logger.exceptions[0]
        self.assertEqual(msg, 'MESSAGE')

    def test_user_info_user(self):
        self.config.testing_securitypolicy(
                userid='hank',
                permissive=True)
        self.registry.settings['exclog.extra_info'] = True
        self.assertRaises(NotImplementedError, self._callFUT)
        self.assertEqual(len(self.logger.exceptions), 1)
        msg = self.logger.exceptions[0]
        self.assertTrue('UNAUTHENTICATED USER\n\nhank' in msg)

    def test_user_info_no_user(self):
        self.registry.settings['exclog.extra_info'] = True
        self.assertRaises(NotImplementedError, self._callFUT)
        self.assertEqual(len(self.logger.exceptions), 1)
        msg = self.logger.exceptions[0]
        self.assertTrue('UNAUTHENTICATED USER\n\n\n' in msg)

    def test_exception_while_logging(self):
        from pyramid.request import Request
        bang = AssertionError('bang')
        class BadRequest(Request):
            @property
            def url(self):
                raise bang
        request = BadRequest.blank('/')
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
        self.assertEqual(self._callFUT(request), 'http://example.com')

    def test_w_deocode_error_wo_qs(self):
        from pyramid.request import Request
        request = Request.blank('/')
        request.environ['SCRIPT_NAME'] = '/script'
        request.environ['PATH_INFO'] = '/path/with/latin1/\x80'
        self.assertEqual(self._callFUT(request),
                         r"could not decode url: " +
                         r"'http://localhost/script/path/with/latin1/\x80'")

    def test_w_deocode_error_w_qs(self):
        from pyramid.request import Request
        request = Request.blank('/')
        request.environ['SCRIPT_NAME'] = '/script'
        request.environ['PATH_INFO'] = '/path/with/latin1/\x80'
        request.environ['QUERY_STRING'] = 'foo=bar'
        self.assertEqual(self._callFUT(request),
                         r"could not decode url: " +
                         r"'http://localhost/script/path/with/latin1/\x80" +
                         r"?foo=bar'")


class Test__get_message(unittest.TestCase):

    def _callFUT(self, request):
        from pyramid_exclog import _get_message
        return _get_message(request)

    def test_evil_encodings(self):
        from pyramid.request import Request
        request = Request.blank('/%FA') # not utf-8
        msg = self._callFUT(request)
        self.assertTrue("could not decode url: 'http://localhost/" in msg)

    def test_evil_encodings_extra_info(self):
        from pyramid.request import Request
        request = Request.blank('/url?%FA=%FA') # not utf-8
        msg = self._callFUT(request)
        self.assertTrue("could not decode params" in msg, msg)

    def test_evil_encodings_extra_info_POST(self):
        from pyramid.request import Request
        request = Request.blank('/url',
                                content_type=
                                    'application/x-www-form-urlencoded; '
                                    'charset=utf-8',
                                POST='%FA=%FA') # not utf-8
        self._callFUT(request) # doesn't fail


class Test_includeme(unittest.TestCase):
    def _callFUT(self, config):
        from pyramid_exclog import includeme
        return includeme(config)

    def test_it(self):
        from pyramid.httpexceptions import WSGIHTTPException
        from pyramid.tweens import EXCVIEW
        config = DummyConfig()
        self._callFUT(config)
        self.assertEqual(config.tweens,
             [('pyramid_exclog.exclog_tween_factory', EXCVIEW, None)])
        self.assertEqual(config.registry.settings['exclog.ignore'],
                         (WSGIHTTPException,))

    def test_it_catchall(self):
        from pyramid.tweens import EXCVIEW
        config = DummyConfig()
        config.settings['exclog.catchall'] = 'true'
        self._callFUT(config)
        self.assertEqual(config.tweens,
                   [('pyramid_exclog.exclog_tween_factory', EXCVIEW,
                     None)])

    def test_it_withignored_builtin(self):
        config = DummyConfig()
        config.settings['exclog.ignore'] = 'NotImplementedError'
        self._callFUT(config)
        self.assertEqual(config.registry.settings['exclog.ignore'],
                         (NotImplementedError,))

    def test_it_withignored_nonbuiltin(self):
        config = DummyConfig()
        config.settings['exclog.ignore'] ='pyramid_exclog.tests.DummyException'
        self._callFUT(config)
        self.assertEqual(config.registry.settings['exclog.ignore'],
                         (DummyException,))

    def test_it_with_extra_info(self):
        config = DummyConfig()
        config.settings['exclog.extra_info'] = 'true'
        self._callFUT(config)
        self.assertEqual(config.registry.settings['exclog.extra_info'], True)

    def test_it_with_get_message(self):
        config = DummyConfig()
        get_message = lambda req: 'MESSAGE'
        config.settings['exclog.get_message'] = get_message
        self._callFUT(config)
        self.assertEqual(config.registry.settings['exclog.get_message'],
                         get_message)

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
