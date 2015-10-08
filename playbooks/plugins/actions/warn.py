# Copyright 2015, Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import getpass
import logging

import ansible

from ansible import utils
from ansible.runner.return_data import ReturnData


class ActionModule(object):
    ''' Fail with custom message '''

    TRANSFERS_FILES = False

    def __init__(self, runner):
        self.runner = runner

    @staticmethod
    def _load_logging():
        mypid = str(os.getpid())
        user = getpass.getuser()
        name = 'Ansible-Warn   | '
        log = logging.getLogger(name)
        for handler in log.handlers:
            if name == handler.name:
                return log
        else:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.DEBUG)
            stream_handler.name = name
            stream_format = logging.Formatter('%(asctime)s - %(name)s%(levelname)s => %(message)s')
            stream_handler.setFormatter(stream_format)

            log.setLevel(logging.DEBUG)
            log.addHandler(stream_handler)
            return log

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):

        # note: the fail module does not need to pay attention to check mode
        # it always runs.

        args = {}
        if complex_args:
            args.update(complex_args)
        args.update(utils.parse_kv(module_args))

        logger = self._load_logging()
        logger.warn(args['msg'])
        result = dict(failed=False, warn=True, msg=args['msg'])
        return ReturnData(conn=conn, result=result)
