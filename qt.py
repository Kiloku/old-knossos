import os
import logging

default_variant = 'PySide'

env_api = os.environ.get('QT_API', 'pyside')
if env_api == 'pyside':
    variant = 'PySide'
elif env_api == 'pyqt':
    variant = 'PyQt4'
elif env_api == 'headless':
    variant = 'headless'
else:
    variant = default_variant

if variant == 'PySide':
    try:
        from PySide import QtGui, QtCore
    except ImportError:
        # Fallback to PyQt4
        variant = 'PyQt4'

if variant == 'PyQt4':
    try:
        import sip
        api2_classes = [
            'QData', 'QDateTime', 'QString', 'QTextStream',
            'QTime', 'QUrl', 'QVariant',
        ]

        for cl in api2_classes:
            sip.setapi(cl, 2)

        from PyQt4 import QtGui, QtCore
        
        QtCore.Signal = QtCore.pyqtSignal
        QtCore.QString = str
    except ImportError:
        # Fallback to headless
        variant = 'headless'

if variant == 'headless':
    if env_api != 'headless':
        logging.warning('Falling back to headless mode. This will most likely fail if you want to use the mod manager!')

    # This is just a dummy implementation of the Qt.Signal() system. Nothing else is provided by this variant.
    import threading
    import time

    _main_loop = None

    class _App(object):
        _running = True
        _queue = None
        _queue_lock = None

        def __init__(self, args):
            global _main_loop

            _main_loop = self
            self._queue = []
            self._queue_lock = threading.Lock()

        def schedule(self, cb, args):
            with self._queue_lock:
                self._queue.append((cb, args))

        def quit(self):
            self._running = False

        def exit(self, code=0):
            self._running = False

        def exec_(self):
            while self._running:
                time.sleep(0.3)

                with self._queue_lock:
                    q = self._queue
                    self._queue = []

                for cb, args in q:
                    cb(*args)

    class _Signal(object):
        _listeners = None
        _lock = None

        def __init__(self, *argtypes):
            # NOTE: Since this is just a dummy implementation, I won't check the argtypes...
            self._listeners = []
            self._lock = threading.Lock()

        def connect(self, cb):
            with self._lock:
                self._listeners.append(cb)

        def disconnect(self, cb):
            with self._lock:
                self._listeners.remove(cb)

        def emit(self, *args):
            global _main_loop

            with self._lock:
                for cb in self._listeners:
                    _main_loop.schedule(cb, args)

    class QtCore(object):
        QObject = object
        QCoreApplication = _App
        Signal = _Signal

    class QtGui(object):
        QApplication = _App

if variant not in ('PySide', 'PyQt4', 'headless'):
    raise ImportError("Python Variant not specified (%s)" % variant)

__all__ = [QtGui, QtCore, variant]
