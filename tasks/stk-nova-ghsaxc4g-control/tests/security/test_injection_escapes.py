"""Behaviour tests: nothing outside the mounted image may be created or changed.

Every case drives the public entry points the compute driver uses to put
material into a mounted instance image.  The sandbox stands in for the host;
a request that would reach outside the image must fail and must leave the
host side untouched.
"""
import os
import unittest

from nova.virt.disk import api as disk_api

from harness import (CANARY, Meta, PASSWD, SHADOW, Sandbox, password_fixtures)


KEY = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ ' + CANARY
NET = 'auto lo\niface lo inet loopback\n'


class EscapeTest(unittest.TestCase):
    def setUp(self):
        self.sandbox = Sandbox()
        self.sandbox.install()
        self.addCleanup(self.sandbox.remove)

    def refused(self, func, *args, **kwargs):
        before = self.sandbox.outside_snapshot()
        try:
            func(*args, **kwargs)
        except Exception:
            pass
        else:
            self.fail('the request was accepted instead of being refused')
        self.assertEqual(before, self.sandbox.outside_snapshot(),
                         'the refused request changed something outside the '
                         'image')

    def test_personality_parent_traversal_is_refused(self):
        self.refused(disk_api.inject_files, 'image',
                     [('../outside/escaped', 'owned')])
        self.assertFalse(os.path.exists(self.sandbox.outside_path('escaped')))

    def test_personality_symlinked_directory_is_refused(self):
        self.sandbox.link(self.sandbox.outside, self.sandbox.path('etc'))
        self.refused(disk_api.inject_files, 'image',
                     [('/etc/escaped', 'owned')])
        self.assertFalse(os.path.exists(self.sandbox.outside_path('escaped')))

    def test_personality_symlinked_file_is_refused(self):
        target = self.sandbox.outside_path('host-file')
        self.sandbox.write(target, 'original')
        self.sandbox.link(target, self.sandbox.path('motd'))
        self.refused(disk_api.inject_files, 'image',
                     [('/motd', 'owned')])
        self.assertEqual(open(target).read(), 'original')

    def test_personality_prefix_sibling_is_refused(self):
        # A path that shares the mount point's leading characters but is a
        # different directory must not be treated as inside it.
        self.refused(disk_api.inject_files, 'image',
                     [('../mnte/escaped', 'owned')])
        self.assertFalse(os.path.exists(os.path.join(self.sandbox.prefix,
                                                     'escaped')))

    def test_personality_directory_side_effect_is_refused(self):
        # The refusal must happen before the parent directory is created.
        self.refused(disk_api.inject_files, 'image',
                     [('../outside/newdir/escaped', 'owned')])
        self.assertFalse(os.path.isdir(self.sandbox.outside_path('newdir')))


if __name__ == '__main__':
    unittest.main()
