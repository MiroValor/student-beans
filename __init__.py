from .base import BaseProvider
from .unidays import UniDaysProvider
from .studentbeans import StudentBeansProvider

_PROVIDERS = {
    "unidays": UniDaysProvider(),
    "studentbeans": StudentBeansProvider(),
}


def get_provider(service: str):
    return _PROVIDERS.get(service.lower())


def list_providers():
    return list(_PROVIDERS.keys())
