# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2015, Kevin Carter <kevin.carter@rackspace.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

import fcntl
import functools
import gettext
import hmac
import os
import pipes
import pty
import pwd
import re
import select
import shlex
import subprocess
import time

from hashlib import sha1

import ansible.constants as C

from ansible.callbacks import vvv
from ansible import errors
from ansible import utils


def retry(exception, tries=3, delay=1):
    """Retry calling the decorated function."""

    def deco_retry(f):
        @functools.wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exception as exp:
                    vvv('Retry Error: Exception details -- "%s"' % exp)
                    time.sleep(mdelay)
                    mtries -= 1
            return f(*args, **kwargs)
        return f_retry
    return deco_retry


class BaseSshError(object):
    def __init__(self, *args, **kwargs):
        if len(args) > 1:
            error_msg = args[0] % args[1:]
        else:
            error_msg = args[0]

        vvv('RUNTIME ERROR: %s' % error_msg)
        raise kwargs.get('exception', errors.AnsibleError)(error_msg)


class BlockCtl(object):
    """Mark an FD as non-blocking."""

    def __init__(self, fd):
        self.fd = fd

    def non_blocking(self):
        fcntl.fcntl(
            self.fd,
            fcntl.F_SETFL,
            fcntl.fcntl(self.fd, fcntl.F_GETFL) | os.O_NONBLOCK
        )

    def un_blocking(self):
        fcntl.fcntl(
            self.fd,
            fcntl.F_SETFL,
            fcntl.fcntl(self.fd, fcntl.F_GETFL) & ~os.O_NONBLOCK
        )


class LockCtl(object):
    """Lock file context manager."""

    def __init__(self, lock_file):
        self.lock_file = lock_file
        self.locked = False

    def __enter__(self):
        self.lock()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unlock()

    def lock(self):
        fcntl.lockf(self.lock_file, fcntl.LOCK_EX)
        self.locked = True
        return self

    def unlock(self):
        fcntl.lockf(self.lock_file, fcntl.LOCK_UN)
        self.locked = False


class Connection(object):
    """ssh based connections."""

    def __init__(self, runner, host, port, user, password, private_key_file,
                 *args, **kwargs):
        self.runner = runner
        self.host = host
        self.ipv6 = ':' in self.host
        self.port = port
        self.user = str(user)
        self.password = password
        self.private_key_file = private_key_file
        self.HASHED_KEY_MAGIC = "|1|"
        self.has_pipelining = True
        self.common_args = list()
        self.become_methods_supported = ['sudo', 'su', 'pbrun']

        with LockCtl(lock_file=self.runner.process_lockfile):
            self.cp_dir = utils.prepare_writeable_dir(
                '$HOME/.ansible/cp', mode=0o700
            )

    def _ssh_option_add(self, options):
        if not isinstance(options, list):
            options = [options]

        for option in options:
            self.common_args.extend(['-o', option])

    def connect(self):
        """connect to the remote host."""

        vvv("ESTABLISH CONNECTION FOR USER: %s" % self.user, host=self.host)
        control_path = C.ANSIBLE_SSH_CONTROL_PATH % {'directory': self.cp_dir}
        if C.ANSIBLE_SSH_ARGS is not None:
            self.common_args.extend(
                [
                    i.strip() for i in shlex.split(C.ANSIBLE_SSH_ARGS)
                    if i.strip()
                ]
            )
        else:
            self._ssh_option_add(["ControlMaster=auto", "ControlPersist=60s"])

        cp_in_use = False
        cp_path_set = False
        for arg in self.common_args:
            if "ControlPersist" in arg:
                cp_in_use = True
            if "ControlPath" in arg:
                cp_path_set = True

        if cp_in_use and not cp_path_set:
            self._ssh_option_add('ControlPath="%s"' % control_path)

        if not C.HOST_KEY_CHECKING:
            self._ssh_option_add("StrictHostKeyChecking=no")

        if self.port:
            self._ssh_option_add("Port=%d" % self.port)

        if self.private_key_file or self.runner.private_key_file:
            if self.private_key_file:
                key_file = self.private_key_file
            elif self.runner.private_key_file:
                key_file = self.runner.private_key_file
            else:
                raise BaseSshError('Option constructor error')
            self._ssh_option_add(
                "IdentityFile=\"%s\"" % os.path.expanduser(key_file)
            )

        if self.password:
            self._ssh_option_add(
                ["GSSAPIAuthentication=no", "PubkeyAuthentication=no"]
            )
        else:
            self._ssh_option_add(
                [
                    "KbdInteractiveAuthentication=no",
                    "PreferredAuthentications=gssapi-with-mic,gssapi-keyex,"
                    "hostbased,publickey",
                    "PasswordAuthentication=no"
                ]
            )
        if self.user != pwd.getpwuid(os.geteuid())[0]:
            self._ssh_option_add("User=%s" % self.user)

        self._ssh_option_add("ConnectTimeout=%d" % self.runner.timeout)

        return self

    @staticmethod
    def _popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
               stderr=subprocess.PIPE):
        return subprocess.Popen(
            cmd,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr
        )

    def _run(self, cmd, indata):
        vvv("RUN COMMAND: %s" % ' '.join(cmd), host=self.host)
        slave = None
        try:
            if indata:
                raise AttributeError('Input data was already defined')
            master, slave = pty.openpty()  # try to use upseudo-pty
        except (AttributeError, OSError):
            p = self._popen(cmd)
            return p, p.stdin
        else:
            p = self._popen(cmd, stdin=slave)
            return p, os.fdopen(master, 'w', 0)
        finally:
            if slave is not None:
                os.close(slave)

    def _password_cmd(self):
        if self.password:
            try:
                p = self._popen(["sshpass"])
                p.communicate()
            except OSError:
                raise BaseSshError(
                    "to use the 'ssh' connection type with passwords,"
                    " you must install the sshpass program"
                )
            else:
                self.rfd, self.wfd = os.pipe()
                ssh_pass_cmd_list = ["sshpass", "-d%d" % self.rfd]
                os.close(self.rfd)
                return ssh_pass_cmd_list
        return list()

    def _send_password(self):
        if self.password:
            try:
                os.write(self.wfd, "%s\n" % self.password)
            finally:
                os.close(self.wfd)

    @retry(BaseSshError, tries=3, delay=2)
    def _communicate(self, p, stdin, indata, sudoable=False, prompt=None):
        """Process a communication socket to a target host."""

        BlockCtl(p.stdout).non_blocking()
        BlockCtl(p.stderr).un_blocking()
        stdout = ''
        stderr = ''
        rpipes = [p.stdout, p.stderr]

        if self.runner.become and sudoable:
            incorrect_password = gettext.dgettext(
                self.runner.become_method,
                C.BECOME_ERROR_STRINGS[self.runner.become_method]
            )

            ipc = "%s\r\n%s" % (incorrect_password, prompt)
            if prompt and stdout.endswith(ipc):
                raise BaseSshError('Incorrect become password')
            elif stdout.endswith(prompt):
                raise BaseSshError('Missing become password')

        try:
            if indata and not stdin.closed:
                stdin.write(indata)
                stdin.close()  # close stdin as soon as its been written

            # Read stdout/stderr from process
            while True:
                rfd, _, _ = select.select(rpipes, [], rpipes, 1)

                if p.stdout in rfd:
                    dat = os.read(p.stdout.fileno(), 9216)
                    stdout += dat
                    if not dat:
                        rpipes.remove(p.stdout)

                if p.stderr in rfd:
                    dat = os.read(p.stderr.fileno(), 9216)
                    stderr += dat
                    if not dat:
                        rpipes.remove(p.stderr)

                if (not rpipes or not rfd) and p.poll() is not None:
                    break
                elif not rpipes and p.poll() is None:
                    p.wait()
                    break
        except Exception as exp:
            raise BaseSshError(
                'SSH Error: data could not be sent to the remote host.'
                ' Make sure this host can be reached over ssh.'
                ' details: %s', exp
            )
        else:
            return p.returncode, stdout, stderr
        finally:
            stdin.close()

    def not_in_host_file(self, host):
        """Check if an entry is in the host file."""

        user_home = os.environ.get('HOME', '~')
        known_hosts = list()
        known_hosts.append(os.path.join(user_home, '.ssh/known_hosts'))
        known_hosts.append("/etc/ssh/ssh_known_hosts")
        known_hosts.append("/etc/ssh/ssh_known_hosts2")

        for hf in known_hosts:
            try:
                with open(hf) as f:
                    host_file_lines = f.readlines()
            except (IOError, OSError):
                continue

            for line in host_file_lines:
                tokens = line.strip().split()
                if not tokens:
                    continue
                if tokens[0].find(self.HASHED_KEY_MAGIC) == 0:
                    # this is a hashed known host entry
                    try:
                        token_index = tokens[0][len(self.HASHED_KEY_MAGIC):]
                        token_split = token_index.split("|", 2)
                        kn_salt, kn_host = token_split
                        _hash = hmac.new(
                            kn_salt.decode('base64'),
                            digestmod=sha1
                        )
                        _hash.update(host)
                        if _hash.digest() == kn_host.decode('base64'):
                            return False
                    except Exception:
                        continue  # invalid hashed host key, skip it
                else:
                    if host in tokens[0]:  # standard host file entry
                        return False
        else:
            return True

    def _command_preflight(self, sudoable):
        stop_list = [
            sudoable,
            self.runner.become,
            self.runner.become_method not in self.become_methods_supported,
        ]

        if all(stop_list):
            raise BaseSshError(
                "Internal Error: this module does not support running"
                " commands via %s", self.runner.become_method
            )

    def _ssh_cmd_setup(self, cmd, become_user, sudoable, executable, in_data):
        ssh_cmd = self._password_cmd()
        ssh_cmd.extend(["ssh", "-C"])
        if not in_data:
            ssh_cmd.append("-tt")

        if utils.VERBOSITY > 3:
            ssh_cmd.append("-vvv")
        else:
            ssh_cmd.append("-v")

        ssh_cmd.extend(self.common_args)

        if self.ipv6:
            ssh_cmd.append('-6')

        ssh_cmd.append(self.host)

        prompt = success_key = None
        if self.runner.become and sudoable:
            becomecmd, prompt, success_key = utils.make_become_cmd(
                cmd,
                become_user,
                executable,
                self.runner.become_method,
                '',
                self.runner.become_exe
            )
            ssh_cmd.append(becomecmd)
        else:
            ssh_cmd.append(executable + ' -c ' + pipes.quote(cmd))

        return ssh_cmd, prompt, success_key

    def _sudoable_cmd(self, success_key, prompt, p, stdin, sudoable,
                      no_prompt_out, no_prompt_err):
        """Setup and run a sudoable command."""

        BlockCtl(fd=p.stdout).non_blocking()
        BlockCtl(fd=p.stderr).non_blocking()

        become_output = ''
        become_errput = ''
        breakout = [
            success_key in become_output,
            prompt and become_output.endswith(prompt),
            utils.su_prompts.check_su_prompt(become_output)
        ]
        while not any(breakout):
            rfd, _, _ = select.select(
                [p.stdout, p.stderr],
                [],
                [p.stdout],
                self.runner.timeout
            )
            if p.stderr in rfd:
                chunk = p.stderr.read()
                if not chunk:
                    raise BaseSshError(
                        'ssh connection closed waiting for a privilege'
                        ' escalation password prompt'
                    )
                become_errput += chunk
                incorrect_password = gettext.dgettext(
                    "become", "Sorry, try again."
                )
                become_err_check = "%s%s" % (prompt, incorrect_password)
                if become_errput.strip().endswith(become_err_check):
                    raise BaseSshError('Incorrect become password')
                elif prompt and become_errput.endswith(prompt):
                    stdin.write(self.runner.become_pass + '\n')

            if p.stdout in rfd:
                chunk = p.stdout.read()
                if not chunk:
                    raise BaseSshError(
                        'ssh connection closed waiting for %s password'
                        ' prompt', self.runner.become_method
                    )
                become_output += chunk

            if not rfd:
                # timeout. wrap up process communication
                p.communicate()
                raise BaseSshError(
                    'ssh connection error while waiting for %s password'
                    ' prompt', self.runner.become_method
                )

        if success_key in become_output:
            no_prompt_out += become_output
            no_prompt_err += become_errput
        elif sudoable:
            stdin.write(self.runner.become_pass + '\n')

        return no_prompt_out, no_prompt_err

    @retry(BaseSshError, tries=3, delay=1)
    def exec_command(self, cmd, tmp_path, become_user=None, sudoable=False,
                     executable='/bin/sh', in_data=None):
        """run a command on the remote host."""

        self._command_preflight(sudoable=sudoable)
        ssh_cmd, prompt, success_key = self._ssh_cmd_setup(
            cmd,
            become_user,
            sudoable,
            executable,
            in_data
        )

        with LockCtl(self.runner.process_lockfile):
            with LockCtl(self.runner.output_lockfile):
                # create process
                p, stdin = self._run(ssh_cmd, in_data)
                self._send_password()

                no_prompt_out = ''
                no_prompt_err = ''
                if sudoable and self.runner.become and self.runner.become_pass:
                    no_prompt_out, no_prompt_err = self._sudoable_cmd(
                        success_key,
                        prompt,
                        p,
                        stdin,
                        sudoable,
                        no_prompt_out,
                        no_prompt_err
                    )

                vvv("EXEC %s" % ' '.join(ssh_cmd), host=self.host)
                returncode, stdout, stderr = self._communicate(
                    p,
                    stdin,
                    in_data,
                    sudoable=sudoable,
                    prompt=prompt
                )

        ssh_pass_impossible = [
            ssh_cmd[0] == "sshpass",
            p.returncode == 6
        ]
        if all(ssh_pass_impossible):
            raise BaseSshError(
                'Using a SSH password instead of a key is not possible'
                ' because Host Key checking is enabled and sshpass does'
                ' not support this.  Please add this host\'s fingerprint'
                ' to your known_hosts file to manage this host.'
            )

        control_persist_errors = [
            'Bad configuration option: ControlPersist' in stderr,
            'unknown configuration option: ControlPersist' in stderr
        ]
        if p.returncode != 0 and any(control_persist_errors):
            raise BaseSshError(
                'using -c ssh on certain older ssh versions may not support'
                ' ControlPersist, set ANSIBLE_SSH_ARGS="" (or ssh_args in'
                ' [ssh_connection] section of the config file) before running'
                ' again'
            )
        elif p.returncode == 255:
            if in_data or self.runner.module_name == 'raw':
                raise BaseSshError(
                    'SSH Error: data could not be sent to the remote host.'
                    ' Make sure this host can be reached over ssh'
                )
            else:
                ip = None
                port = None
                for line in stderr.splitlines():
                    match = re.search(
                        'Connecting to .*\[(\d+\.\d+\.\d+\.\d+)\] port (\d+)',
                        line
                    )
                    if match:
                        ip = match.group(1)
                        port = match.group(2)

                if 'UNPROTECTED PRIVATE KEY FILE' in stderr:
                    lines = [
                        line for line in stderr.splitlines()
                        if 'ignore key:' in line
                    ]
                else:
                    lines = stderr.splitlines()[-1:]

                if ip and port:
                    lines.append('\twhile connecting to %s:%s' % (ip, port))

                lines.append(
                    'It is sometimes useful to re-run the command using'
                    ' -vvvv, which prints SSH debug output to help diagnose'
                    ' the issue.'
                )
                raise BaseSshError('SSH Error: %s', '\n'.join(lines))

        return p.returncode, '', no_prompt_out + stdout, no_prompt_err + stderr

    @retry(BaseSshError, tries=3, delay=1)
    def put_file(self, in_path, out_path):
        """transfer a file from local to remote."""

        vvv("PUT %s TO %s" % (in_path, out_path), host=self.host)
        if not os.path.exists(in_path):
            raise BaseSshError(
                "file or module does not exist: %s", in_path,
                exception=errors.AnsibleFileNotFound,
            )

        cmd = self._password_cmd()
        host = self.host
        if self.ipv6:
            host = '[%s]' % host

        indata = None
        if C.DEFAULT_SCP_IF_SSH:
            cmd.append("scp")
            cmd.extend(self.common_args)
            cmd.extend([in_path, host + ":" + pipes.quote(out_path)])
        else:
            cmd.append("sftp")
            cmd.extend(self.common_args)
            cmd.append(host)
            indata = "put %s %s\n" % (
                pipes.quote(in_path),
                pipes.quote(out_path)
            )

        p, stdin = self._run(cmd, indata)
        self._send_password()
        BlockCtl(p.stderr).non_blocking()
        BlockCtl(p.stdout).non_blocking()
        returncode, stdout, stderr = self._communicate(p, stdin, indata)
        if returncode != 0:
            raise BaseSshError(
                "failed to transfer file to %s:\n%s\n%s",
                out_path,
                stdout,
                stderr
            )

    @retry(BaseSshError, tries=3, delay=1)
    def fetch_file(self, in_path, out_path):
        """fetch a file from remote to local."""

        vvv("FETCH %s TO %s" % (in_path, out_path), host=self.host)
        cmd = self._password_cmd()

        host = self.host
        if self.ipv6:
            host = '[%s]' % host

        indata = None
        if C.DEFAULT_SCP_IF_SSH:
            cmd.append("scp")
            cmd.extend(self.common_args)
            cmd.extend([host + ":" + in_path, out_path])
        else:
            cmd.append("sftp")
            cmd.extend(self.common_args)
            cmd.append(host)
            indata = "get %s %s\n" % (in_path, out_path)

        p = self._popen(cmd)
        self._send_password()
        BlockCtl(p.stderr).non_blocking()
        BlockCtl(p.stdout).non_blocking()
        stdout, stderr = p.communicate(indata)
        if p.returncode != 0:
            raise BaseSshError(
                "failed to transfer file from %s:\n%s\n%s",
                in_path,
                stdout,
                stderr
            )

    def close(self):
        pass
