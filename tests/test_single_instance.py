import os
import socket
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.mirro_core as mirro_core


class PortBusyTest(unittest.TestCase):
    """Второй экземпляр Mirro не должен молча занимать занятый порт."""

    def test_busy_port_is_detected(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        try:
            self.assertTrue(mirro_core._port_is_busy("127.0.0.1", port))
        finally:
            listener.close()

    def test_free_port_is_not_busy(self):
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()
        self.assertFalse(mirro_core._port_is_busy("127.0.0.1", port))

    def test_wildcard_host_checks_loopback(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        try:
            self.assertTrue(mirro_core._port_is_busy("0.0.0.0", port))
        finally:
            listener.close()


if __name__ == "__main__":
    unittest.main()
