'''
Namespace composition and internals.
'''

from . import builtins, interns, operators
from ..datatypes import aletheia
from ..datatypes import iris
from ..internal.presets import STDLIB_NAMES, STDLIB_PREFIX

namespace = interns.__dict__ | iris.__dict__ | aletheia.__dict__ | operators.__dict__ | builtins.__dict__
stdvalues = {STDLIB_NAMES[k[len(STDLIB_PREFIX):]]: v for k, v in namespace.items() if STDLIB_PREFIX in k}
stdtypes = {k: aletheia.infer(v) for k, v in stdvalues.items()}