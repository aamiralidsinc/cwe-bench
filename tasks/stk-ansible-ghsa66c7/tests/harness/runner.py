# -*- coding: utf-8 -*-
"""Drive the product's own command-line tool with a playbook.

Every hidden test goes through ``ansible-playbook``: the playbook is written to a
temporary directory, the CLI is run as the unprivileged verifier user, and the
result is returned together with its combined output.  Markers are files the
payload would create only if it were executed.
"""

import os
import subprocess
import sys
import tempfile

WORKSPACE = os.environ.get("ANSIBLE_WORKSPACE", "/workspace")
HERE = os.path.dirname(os.path.abspath(__file__))
LIBRARY = os.path.join(HERE, "library")


class Run(object):
    def __init__(self, returncode, output):
        self.returncode = returncode
        self.output = output

    @property
    def ok(self):
        return self.returncode == 0

    def report(self):
        return "exit %s\n%s" % (self.returncode, self.output[-4000:])


def marker(name):
    """A path inside a private temporary directory; it must never appear."""
    directory = tempfile.mkdtemp(prefix="ansible-value-")
    return os.path.join(directory, name)


def _quoted(text):
    # A YAML double-quoted scalar for the value.
    return '"%s"' % text.replace("\\", "\\\\").replace('"', '\\"')


def run_playbook(source):
    work = tempfile.mkdtemp(prefix="ansible-play-")
    path = os.path.join(work, "play.yml")
    handle = open(path, "w")
    try:
        handle.write(source)
    finally:
        handle.close()

    python = sys.executable
    command = [python, os.path.join(WORKSPACE, "bin", "ansible-playbook"),
               "-i", "localhost,", "-e",
               "ansible_python_interpreter=%s" % python, path]
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(WORKSPACE, "lib")
    env["ANSIBLE_LIBRARY"] = os.pathsep.join(
        [LIBRARY, os.path.join(WORKSPACE, "library")])
    env["ANSIBLE_NOCOLOR"] = "1"
    env["ANSIBLE_FORCE_COLOR"] = "0"
    env.pop("ANSIBLE_CONFIG", None)

    process = subprocess.Popen(command, cwd=work, env=env,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    output = process.communicate()[0]
    return Run(process.returncode, output)


HEAD = ("- hosts: localhost\n"
        "  connection: local\n"
        "  gather_facts: no\n")


def loop_play(value):
    return (HEAD +
            "  vars:\n"
            "    items_text: %s\n"
            "  tasks:\n"
            "    - name: loop over the value\n"
            '      debug: msg="{{ item }}"\n'
            "      with_items: items_text\n" % _quoted(value))


def args_play(value):
    return (HEAD +
            "  vars:\n"
            "    arg_text: %s\n"
            "  tasks:\n"
            "    - name: use the value as task arguments\n"
            "      debug:\n"
            '      args: "{{ arg_text }}"\n' % _quoted(value))


def environment_play(value):
    return (HEAD +
            "  vars:\n"
            "    env_text: %s\n"
            "  tasks:\n"
            "    - name: use the value as the task environment\n"
            '      shell: "true"\n'
            '      environment: "{{ env_text }}"\n' % _quoted(value))


def environment_echo_play(value):
    return (HEAD +
            "  vars:\n"
            "    env_text: %s\n"
            "  tasks:\n"
            "    - name: use the value as the task environment\n"
            '      shell: "printf %%s \\"$GREETING\\""\n'
            '      environment: "{{ env_text }}"\n'
            "      register: out\n"
            '    - debug: msg="env={{ out.stdout }}"\n' % _quoted(value))


def module_mapping_play(value):
    return (HEAD +
            "  vars:\n"
            "    opts_text: %s\n"
            "  tasks:\n"
            "    - name: pass a mapping as text\n"
            "      probe_opts:\n"
            '        opts: "{{ opts_text }}"\n' % _quoted(value))


def module_mapping_play_json(value):
    return (HEAD +
            "  vars:\n"
            "    opts_text: %s\n"
            "  tasks:\n"
            "    - name: pass a mapping as text\n"
            "      probe_opts:\n"
            '        opts: "{{ opts_text }}"\n'
            "      register: out\n"
            '    - debug: msg="got {{ out.got }}"\n' % _quoted(value))


def host_value_play(kind, marker_path=None, extra_vars=""):
    setting = kind
    if marker_path is not None:
        setting = "%s marker=%s" % (kind, marker_path)
    return (HEAD +
            extra_vars +
            "  tasks:\n"
            "    - name: take a value from the host\n"
            "      data_source: kind=%s\n"
            "      register: r\n"
            "    - debug:\n"
            '        msg: "value={{ r.value }}"\n' % setting)


def host_plain_play(kind, extra_vars, expression="r.value"):
    body = (HEAD +
            extra_vars +
            "  tasks:\n"
            "    - name: take a value from the host\n"
            "      data_source: kind=" + kind + "\n"
            "      register: r\n"
            "    - debug:\n"
            '        msg: "value={{ ' + expression + ' }}"\n')
    return body
