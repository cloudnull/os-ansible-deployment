# Copyright 2014, Rackspace US, Inc.
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
#
# (c) 2014, Kevin Carter <kevin.carter@rackspace.com>

import os
import re
import traceback

from ansible import errors
from ansible import utils
import yaml


# Used to keep track of git package parts as various files are processed
GIT_PACKAGE_DEFAULT_PARTS = dict()


REQUIREMENTS_FILE_TYPES = [
    'global-requirements.txt',
    'test-requirements.txt',
    'dev-requirements.txt',
    'requirements.txt',
    'global-requirement-pins.txt'
]


# List of variable names that could be used within the yaml files that
# represent lists of python packages.
BUILT_IN_PIP_PACKAGE_VARS = [
    'service_pip_dependencies',
    'pip_common_packages',
    'pip_container_packages',
    'pip_packages'
]


def git_pip_link_parse(repo):
    """Return a tuple containing the parts of a git repository.

    Example parsing a standard git repo:
      >>> git_pip_link_parse('git+https://github.com/username/repo-name@tag')
      ('repo-name',
       'tag',
       None,
       'https://github.com/username/repo',
       'git+https://github.com/username/repo@tag',
       'repo_name')

    Example parsing a git repo that uses an installable from a subdirectory:
      >>> git_pip_link_parse(
      ...     'git+https://github.com/username/repo@tag#egg=plugin.name'
      ...     '&subdirectory=remote_path/plugin.name'
      ... )
      ('plugin.name',
       'tag',
       'remote_path/plugin.name',
       'https://github.com/username/repo',
       'git+https://github.com/username/repo@tag#egg=plugin.name&'
       'subdirectory=remote_path/plugin.name',
       'plugin.name')

    :param repo: git repo string to parse.
    :type repo: ``str``
    :returns: ``tuple``
    """'meta'

    def _meta_return(meta_data, item):
        """Return the value of an item in meta data."""

        return meta_data.lstrip('#').split('%s=' % item)[-1].split('&')[0]

    _git_url = repo.split('+')
    if len(_git_url) >= 2:
        _git_url = _git_url[1]
    else:
        _git_url = _git_url[0]

    git_branch_sha = _git_url.split('@')
    if len(git_branch_sha) > 2:
        branch = git_branch_sha.pop()
        url = '@'.join(git_branch_sha)
    elif len(git_branch_sha) > 1:
        url, branch = git_branch_sha
    else:
        url = git_branch_sha[0]
        branch = 'master'

    egg_name = name = os.path.basename(url.rstrip('/'))
    egg_name = egg_name.replace('-', '_')

    _branch = branch.split('#')
    branch = _branch[0]

    plugin_path = None
    # Determine if the package is a plugin type
    if len(_branch) > 1:
        if 'subdirectory=' in _branch[-1]:
            plugin_path = _meta_return(_branch[-1], 'subdirectory')
            name = os.path.basename(plugin_path)

        if 'egg=' in _branch[-1]:
            egg_name = _meta_return(_branch[-1], 'egg')
            egg_name = egg_name.replace('-', '_')

        if 'gitname=' in _branch[-1]:
            name = _meta_return(_branch[-1], 'gitname')

    return name.lower(), branch, plugin_path, url, repo, egg_name


def _pip_requirement_split(requirement):
    """Split pip versions from a given requirement.

    The method will return the package name, versions, and any markers.

    :type requirement: ``str``
    :returns: ``tuple``
    """
    version_descriptors = "(>=|<=|>|<|==|~=|!=)"
    requirement = requirement.split(';')
    requirement_info = re.split(r'%s\s*' % version_descriptors, requirement[0])
    name = requirement_info[0]
    marker = None
    if len(requirement) > 1:
        marker = requirement[1]
    versions = None
    if len(requirement_info) > 1:
        versions = requirement_info[1]

    return name, versions, marker


class DependencyFileProcessor(object):
    def __init__(self, local_path):
        """Find required files.

        :type local_path: ``str``
        :return:
        """
        self.pip = dict()
        self.pip['git_package'] = list()
        self.pip['py_package'] = list()
        self.pip['role_packages'] = dict()
        self.pip['git_data'] = list()
        self.git_pip_install = 'git+%s@%s'
        self.file_names = self._get_files(path=local_path)

        # Process everything simply by calling the method
        self._process_files()

    def _py_pkg_extend(self, packages):
        for pkg in packages:
            pkg_name = _pip_requirement_split(pkg)[0]
            for py_pkg in self.pip['py_package']:
                py_pkg_name = _pip_requirement_split(py_pkg)[0]
                if pkg_name == py_pkg_name:
                    self.pip['py_package'].remove(py_pkg)
        self.pip['py_package'].extend(packages)

    @staticmethod
    def _filter_files(file_names, ext):
        """Filter the files and return a sorted list.

        :type file_names:
        :type ext: ``str`` or ``tuple``
        :returns: ``list``
        """
        _file_names = list()
        file_name_words = ['/defaults/', '/vars/', '/user_']
        file_name_words.extend(REQUIREMENTS_FILE_TYPES)
        for file_name in file_names:
            if file_name.endswith(ext):
                if any(i in file_name for i in file_name_words):
                    _file_names.append(file_name)
        else:
            return _file_names

    @staticmethod
    def _get_files(path):
        """Return a list of all files in the defaults/repo_packages directory.

        :type path: ``str``
        :returns: ``list``
        """
        paths = os.walk(os.path.abspath(path))
        files = list()
        for fpath, _, afiles in paths:
            for afile in afiles:
                files.append(os.path.join(fpath, afile))
        else:
            return files

    def _check_plugins(self, git_repo_plugins, git_data):
        """Check if the git url is a plugin type.

        :type git_repo_plugins: ``dict``
        :type git_data: ``dict``
        """
        for repo_plugin in git_repo_plugins:
            strip_plugin_path = repo_plugin['package'].lstrip('/')
            plugin = '%s/%s' % (
                repo_plugin['path'].strip('/'),
                strip_plugin_path
            )

            name = git_data['name'] = os.path.basename(strip_plugin_path)
            git_data['egg_name'] = name.replace('-', '_')
            package = self.git_pip_install % (
                git_data['repo'], git_data['branch']
            )
            package += '#egg=%s' % git_data['egg_name']
            package += '&subdirectory=%s' % plugin
            package += '&gitname=%s' % name
            if git_data['fragments']:
                package += '&%s' % git_data['fragments']

            self.pip['git_data'].append(git_data)
            self.pip['git_package'].append(package)

            if name not in GIT_PACKAGE_DEFAULT_PARTS:
                GIT_PACKAGE_DEFAULT_PARTS[name] = git_data.copy()
            else:
                GIT_PACKAGE_DEFAULT_PARTS[name].update(git_data.copy())

    @staticmethod
    def _check_defaults(git_data, name, item):
        """Check if a default exists and use it if an item is undefined.

        :type git_data: ``dict``
        :type name: ``str``
        :type item: ``str``
        """
        if not git_data[item] and name in GIT_PACKAGE_DEFAULT_PARTS:
            check_item = GIT_PACKAGE_DEFAULT_PARTS[name].get(item)
            if check_item:
                git_data[item] = check_item

    def _process_git(self, loaded_yaml, git_item):
        """Process git repos.

        :type loaded_yaml: ``dict``
        :type git_item: ``str``
        """
        git_data = dict()
        if git_item.split('_')[0] == 'git':
            prefix = ''
        else:
            prefix = '%s_' % git_item.split('_git_repo')[0].replace('.', '_')

        # Set the various variable definitions
        repo_var = prefix + 'git_repo'
        name_var = prefix + 'git_package_name'
        branch_var = prefix + 'git_install_branch'
        fragment_var = prefix + 'git_install_fragments'
        plugins_var = prefix + 'repo_plugins'

        # get the repo definition
        git_data['repo'] = loaded_yaml.get(repo_var)

        # get the repo name definition
        name = git_data['name'] = loaded_yaml.get(name_var)
        if not name:
            name = git_data['name'] = os.path.basename(
                git_data['repo'].rstrip('/')
            )
        git_data['egg_name'] = name.replace('-', '_')

        # get the repo branch definition
        git_data['branch'] = loaded_yaml.get(branch_var)
        self._check_defaults(git_data, name, 'branch')
        if not git_data['branch']:
            git_data['branch'] = 'master'

        package = self.git_pip_install % (git_data['repo'], git_data['branch'])

        # get the repo fragment definitions, if any
        git_data['fragments'] = loaded_yaml.get(fragment_var)
        self._check_defaults(git_data, name, 'fragments')

        package += '#egg=%s' % git_data['egg_name']
        package += '&gitname=%s' % name
        if git_data['fragments']:
            package += '&%s' % git_data['fragments']

        self.pip['git_package'].append(package)
        self.pip['git_data'].append(git_data.copy())

        # Set the default package parts to track data during the run
        if name not in GIT_PACKAGE_DEFAULT_PARTS:
            GIT_PACKAGE_DEFAULT_PARTS[name] = git_data.copy()
        else:
            GIT_PACKAGE_DEFAULT_PARTS[name].update()

        # get the repo plugin definitions, if any
        git_data['plugins'] = loaded_yaml.get(plugins_var)
        self._check_defaults(git_data, name, 'plugins')
        if git_data['plugins']:
            self._check_plugins(
                git_repo_plugins=git_data['plugins'],
                git_data=git_data
            )

    def _process_files(self):
        """Process files."""

        role_name = None
        for file_name in self._filter_files(self.file_names, ('yaml', 'yml')):
            with open(file_name, 'r') as f:
                # If there is an exception loading the file continue
                #  and if the loaded_config is None continue. This makes
                #  no bad config gets passed to the rest of the process.
                try:
                    loaded_config = yaml.safe_load(f.read())
                except Exception:  # Broad exception so everything is caught
                    continue
                else:
                    if not loaded_config:
                        continue

                    if 'roles' in file_name:
                        _role_name = file_name.split('roles%s' % os.sep)[-1]
                        role_name = _role_name.split(os.sep)[0]

            for key, values in loaded_config.items():
                # This conditional is set to ensure we're not processes git
                #  repos from the defaults file which may conflict with what is
                #  being set in the repo_packages files.
                if '/defaults/main' not in file_name:
                    if key.endswith('git_repo'):
                        self._process_git(
                            loaded_yaml=loaded_config,
                            git_item=key
                        )

                if [i for i in BUILT_IN_PIP_PACKAGE_VARS if i in key]:
                    self._py_pkg_extend(values)

                    if role_name:
                        if role_name not in self.pip['role_packages']:
                            self.pip['role_packages'][role_name] = values
                        else:
                            self.pip['role_packages'][role_name].extend(values)
                            self.pip['role_packages'][role_name] = sorted(
                                set(
                                    self.pip['role_packages'][role_name]
                                )
                            )

        for file_name in self._filter_files(self.file_names, 'txt'):
            if os.path.basename(file_name) in REQUIREMENTS_FILE_TYPES:
                with open(file_name, 'r') as f:
                    packages = [
                        i.split()[0] for i in f.read().splitlines()
                        if i
                        if not i.startswith('#')
                    ]
                    self._py_pkg_extend(packages)


def _abs_path(path):
    return os.path.abspath(
        os.path.expanduser(
            path
        )
    )


class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        """Run the lookup module.

        :type basedir:
        :type kwargs:
        """
        self.basedir = basedir

    def run(self, terms, inject=None, **kwargs):
        """Run the main application.

        :type terms: ``str``
        :type inject: ``str``
        :type kwargs: ``dict``
        :returns: ``list``
        """
        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)
        if isinstance(terms, basestring):
            terms = [terms]

        return_data = {
            'packages': set(),
            'remote_packages': set(),
            'remote_package_parts': list(),
            'role_packages': dict()
        }
        for term in terms:
            return_list = list()
            try:
                dfp = DependencyFileProcessor(
                    local_path=_abs_path(str(term))
                )
                return_list.extend(dfp.pip['py_package'])
                return_list.extend(dfp.pip['git_package'])
            except Exception as exp:
                raise errors.AnsibleError(
                    'lookup_plugin.py_pkgs(%s) returned "%s" error "%s"' % (
                        term,
                        str(exp),
                        traceback.format_exc()
                    )
                )

            for item in return_list:
                if item.startswith(('http:', 'https:', 'git+')):
                    if '@' not in item:
                        return_data['packages'].add(item)
                    else:
                        git_parts = git_pip_link_parse(item)
                        item_name = git_parts[-1]
                        if not item_name:
                            item_name = git_pip_link_parse(item)[0]

                        for rpkg in list(return_data['remote_packages']):
                            rpkg_name = git_pip_link_parse(rpkg)[-1]
                            if not rpkg_name:
                                rpkg_name = git_pip_link_parse(item)[0]

                            if rpkg_name == item_name:
                                return_data['remote_packages'].remove(rpkg)
                                return_data['remote_packages'].add(item)
                                break
                        else:
                            return_data['remote_packages'].add(item)
                else:
                    return_data['packages'].add(item)
            else:
                return_data['packages'] = set([
                    i.lower() for i in return_data['packages']
                ])

                keys = [
                    'name',
                    'version',
                    'fragment',
                    'url',
                    'original',
                    'egg_name'
                ]
                remote_pkg_parts = [
                    dict(
                        zip(
                            keys, git_pip_link_parse(i)
                        )
                    ) for i in return_data['remote_packages']
                ]
                return_data['remote_package_parts'].extend(remote_pkg_parts)
                return_data['remote_package_parts'] = list(
                    dict(
                        (i['name'], i)
                        for i in return_data['remote_package_parts']
                    ).values()
                )
                return_data['role_packages'].update(dfp.pip['role_packages'])
        else:
            # Sort everything within the returned data
            for key, value in return_data.items():
                if isinstance(value, (list, set)):
                    return_data[key] = sorted(value)
            return [return_data]


# Used for testing and debuging usage: `python plugins/lookups/py_pkgs.py ../`
if __name__ == '__main__':
    import sys
    import json
    print(json.dumps(LookupModule().run(terms=sys.argv[1:]), indent=4))
