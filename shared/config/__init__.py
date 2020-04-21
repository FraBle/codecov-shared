import os
import logging
from copy import deepcopy

from yaml import safe_load as yaml_load
import collections


class MissingConfigException(Exception):
    pass


log = logging.getLogger(__name__)

default_config = {
    "services": {
        "minio": {
            "host": "minio",
            "access_key_id": "codecov-default-key",
            "secret_access_key": "codecov-default-secret",
            "verify_ssl": False,
            "iam_auth": False,
            "iam_endpoint": None,
            "hash_key": "ab164bf3f7d947f2a0681b215404873e",
        }
    }
}


def update(d, u):
    d = deepcopy(d)
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


class ConfigHelper(object):
    def __init__(self):
        self._params = None
        self.loaded_files = {}

    def load_env_var(self):
        val = {}
        for env_var in os.environ:
            if not env_var.startswith("__"):
                multiple_level_vars = env_var.split("__")
                if len(multiple_level_vars) > 1:
                    current = val
                    for c in multiple_level_vars[:-1]:
                        current = current.setdefault(c.lower(), {})
                    current[multiple_level_vars[-1].lower()] = os.getenv(env_var)
        return val

    @property
    def params(self):
        if self._params is None:
            content = self.yaml_content()
            env_vars = self.load_env_var()
            temp_result = update(default_config, content)
            final_result = update(temp_result, env_vars)
            self.set_params(final_result)
        return self._params

    def set_params(self, val):
        self._params = val

    def get(self, *args, **kwargs):
        current_p = self.params
        for el in args:
            try:
                current_p = current_p[el]
            except (KeyError, TypeError):
                raise MissingConfigException(args)
        return current_p

    def load_yaml_file(self):
        yaml_path = os.getenv("CODECOV_YML", "/config/codecov.yml")
        with open(yaml_path, "r") as c:
            return c.read()

    def yaml_content(self):
        try:
            return yaml_load(self.load_yaml_file())
        except FileNotFoundError:
            return {}

    def load_filename_from_path(self, *args):
        if args not in self.loaded_files:
            with open(self.get(*args), "r") as _file:
                self.loaded_files[args] = _file.read()
        return self.loaded_files[args]


config_class_instance = ConfigHelper()


def _get_config_instance():
    return config_class_instance


def get_config(*path, default=None):
    config = _get_config_instance()
    try:
        return config.get(*path)
    except MissingConfigException:
        return default


def load_file_from_path_at_config(*args):
    config = _get_config_instance()
    return config.load_filename_from_path(*args)


def get_verify_ssl(service):
    verify = get_config(service, "verify_ssl")
    if verify is False:
        return False
    return get_config(service, "ssl_pem") or os.getenv("REQUESTS_CA_BUNDLE")
