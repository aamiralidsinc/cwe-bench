"""Shared support for the behaviour tests.

The product code changes a mounted guest filesystem by running host commands
as the privileged service user.  These tests run that code against a throwaway
sandbox and stand in for those commands.  Each stub acts on the sandbox the way
the privileged command would act on a real host, and records what it touched so
a test can see where a write really landed.
"""
import os
import shutil
import tempfile

from nova import utils as nova_utils
from nova.virt.disk import api as disk_api


CANARY = 'nova-canary-value'


def under(root, path):
    root = os.path.realpath(root)
    path = os.path.realpath(path)
    return path == root or path.startswith(root + os.sep)


class Recorder(object):
    """Stands in for nova.utils.execute and its root-owned commands."""

    def __init__(self, root):
        self.root = root
        self.ops = []

    def _guard(self, path):
        if not under(self.root, path) and not self._is_staging(path):
            raise RuntimeError('test sandbox escape: %s' % path)

    def _is_staging(self, path):
        """A temporary copy the product makes while editing an image file.

        These live in the system temp directory, not in the guest image or
        on the host path the guest path points at.
        """
        real = os.path.realpath(path)
        temp = os.path.realpath(tempfile.gettempdir())
        return (not under(self.root, real)
                and real.startswith(temp + os.sep)
                and os.path.basename(real).startswith('tmp'))

    def _record(self, program, path, write):
        self.ops.append({'program': program, 'path': path,
                         'resolved': os.path.realpath(path), 'write': write})

    def __call__(self, *cmd, **kwargs):
        argv = [str(c) for c in cmd]
        program = argv[0]
        flags = [a for a in argv[1:] if a.startswith('-') and a != '-']
        args = [a for a in argv[1:] if not (a.startswith('-') and a != '-')]
        payload = kwargs.get('process_input')

        if program == 'readlink':
            # -n -m: no trailing newline, canonicalise even if the leaf does
            # not exist.  This runs with the privilege of the real command.
            return os.path.realpath(args[-1]), ''

        if program == 'mkdir':
            for path in args:
                self._guard(path)
                if not os.path.isdir(path):
                    os.makedirs(path)
                self._record('mkdir', path, True)
            return '', ''

        if program == 'tee':
            path = args[0]
            self._guard(path)
            mode = 'ab' if '-a' in flags else 'wb'
            f = open(path, mode)
            try:
                if payload:
                    f.write(payload)
            finally:
                f.close()
            self._record('tee', path, True)
            return '', ''

        if program == 'chmod':
            mode = int(str(args[0]), 8)
            path = args[1]
            self._guard(path)
            os.chmod(path, mode)
            self._record('chmod', path, True)
            return '', ''

        if program == 'chown':
            # The service runs as root; the sandbox owner is the test user.
            path = args[-1]
            self._guard(path)
            self._record('chown', path, True)
            return '', ''

        if program == 'cp':
            src, dst = args[0], args[1]
            self._guard(src)
            self._guard(dst)
            shutil.copy2(src, dst)
            self._record('cp', src, not self._is_staging(src))
            self._record('cp', dst, not self._is_staging(dst))
            return '', ''

        if program == 'touch':
            path = args[0]
            self._guard(path)
            open(path, 'ab').close()
            self._record('touch', path, True)
            return '', ''

        # Image/device plumbing is irrelevant here; it stays inside the sandbox.
        return '', ''


class Sandbox(object):
    def __init__(self):
        self.root = tempfile.mkdtemp(prefix='nova-inject-')
        self.mnt = os.path.join(self.root, 'mnt')
        self.outside = os.path.join(self.root, 'outside')
        self.prefix = os.path.join(self.root, 'mnte')
        for path in (self.mnt, self.outside, self.prefix):
            os.makedirs(path)
        self.recorder = Recorder(self.root)
        self._saved_execute = None
        self._saved_disk_image = None

    def install(self):
        self._saved_execute = nova_utils.execute
        nova_utils.execute = self.recorder

        mount_root = self.mnt

        class FakeDiskImage(object):
            def __init__(self, image, partition=None, use_cow=False,
                         mount_dir=None):
                self.mount_dir = mount_root
                self._errors = []

            @property
            def errors(self):
                return '\n'.join(self._errors)

            def mount(self):
                return True

            def umount(self):
                return

        self._saved_disk_image = disk_api._DiskImage
        disk_api._DiskImage = FakeDiskImage

    def remove(self):
        if self._saved_execute is not None:
            nova_utils.execute = self._saved_execute
        if self._saved_disk_image is not None:
            disk_api._DiskImage = self._saved_disk_image
        shutil.rmtree(self.root, ignore_errors=True)

    # --- fixtures -----------------------------------------------------------
    def path(self, *parts):
        return os.path.join(self.mnt, *parts)

    def outside_path(self, *parts):
        return os.path.join(self.outside, *parts)

    def write(self, path, data):
        parent = os.path.dirname(path)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        f = open(path, 'wb')
        try:
            f.write(data)
        finally:
            f.close()

    def link(self, target, path):
        parent = os.path.dirname(path)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        if os.path.lexists(path):
            os.unlink(path)
        os.symlink(target, path)

    # --- observations -------------------------------------------------------
    def outside_snapshot(self):
        """Everything outside the mounted image, including modes and links."""
        state = {}
        root = os.path.realpath(self.root)
        mnt = os.path.realpath(self.mnt)
        for dirpath, dirnames, filenames in os.walk(root):
            if dirpath == mnt or dirpath.startswith(mnt + os.sep):
                continue
            for name in sorted(dirnames + filenames):
                path = os.path.join(dirpath, name)
                rel = os.path.relpath(path, root)
                st = os.lstat(path)
                if os.path.islink(path):
                    state[rel] = ('link', os.readlink(path))
                elif os.path.isdir(path):
                    state[rel] = ('dir', st.st_mode & 07777, st.st_mtime)
                else:
                    f = open(path, 'rb')
                    try:
                        data = f.read()
                    finally:
                        f.close()
                    state[rel] = ('file', data, st.st_mode & 07777,
                                  st.st_mtime)
        return state

    def writes_outside(self):
        return [op for op in self.recorder.ops
                if op['write'] and not under(self.mnt, op['resolved'])]

    def writes_inside(self, path):
        return [op for op in self.recorder.ops
                if op['write'] and os.path.realpath(op['resolved']) ==
                os.path.realpath(path)]


class Meta(object):
    def __init__(self, key, value):
        self.key = key
        self.value = value


PASSWD = ('root:x:0:0:root:/root:/bin/bash\n'
          'nobody:x:65534:65534:nobody:/nonexistent:/bin/false\n')
SHADOW = ('root:$6$abcdefgh$0123456789abcdefghijklmnopqrstuvwxyz:15000:0:'
          '99999:7:::\n'
          'nobody:!:15000:0:99999:7:::\n')


def password_fixtures(root):
    """Create a normal-looking passwd/shadow pair below `root`."""
    if not os.path.isdir(root):
        os.makedirs(root)
    f = open(os.path.join(root, 'passwd'), 'wb')
    try:
        f.write(PASSWD)
    finally:
        f.close()
    f = open(os.path.join(root, 'shadow'), 'wb')
    try:
        f.write(SHADOW)
    finally:
        f.close()
