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
        msg = self.logger.exceptions[0]
        self.assertTrue('ENVIRONMENT' in msg)
        
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

class DummyException(object):
    pass

class DummyLogger(object):
    def __init__(self):
        self.exceptions = []

    def exception(self, msg):
        self.exceptions.append(msg)

class DummyConfig(object):
    def __init__(self):
        self.tweens = []
        self.registry = self
        self.settings = {}

    def add_tween(self, factory, under=None, over=None):
        self.tweens.append((factory, under, over))

