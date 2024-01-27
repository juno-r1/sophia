'''
Namespace composition and internals.
'''
import re

from . import builtins, operators
from ..datatypes import aletheia
from ..datatypes import iris
from ..internal.presets import STDLIB_NAMES, STDLIB_PREFIX

def intern_namespace(
	namespace: dict[str]
	) -> dict[str]:

	return {k: v for k, v in namespace.items() if not (k in STDLIB_NAMES.values())}

def user_namespace(
	namespace: dict[str]
	) -> dict[str]:

	return {k: v for k, v in namespace.items() if not (k in STDLIB_NAMES.values() or re.fullmatch(r'-?[0123456789]+', k))}

namespace = iris.__dict__ | aletheia.__dict__ | operators.__dict__ | builtins.__dict__
stdvalues = {STDLIB_NAMES[k[len(STDLIB_PREFIX):]]: v for k, v in namespace.items() if STDLIB_PREFIX in k}
stdtypes = {k: aletheia.infer(v) for k, v in stdvalues.items()}