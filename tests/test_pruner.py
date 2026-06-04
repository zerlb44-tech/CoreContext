import pytest
import ast
from src.pruner import prune_code_string

def test_prune_docstrings():
    code = '''
"""Module docstring."""
class MyClass:
    """Class docstring."""
    def method(self):
        """Method docstring."""
        x = 1
        return x
'''
    pruned = prune_code_string(code)
    
    # Docstrings should be removed
    assert "Module docstring" not in pruned
    assert "Class docstring" not in pruned
    assert "Method docstring" not in pruned
    # Code logic should be preserved (though method body gets pruned by default, let's keep class/method signatures)
    assert "class MyClass" in pruned
    assert "def method(self)" in pruned

def test_prune_logging_and_prints():
    # If a method is marked critical, we keep its body, but strip its loggers
    code = '''
import logging
logger = logging.getLogger("test")

def critical_func():
    """Docstring."""
    print("Should be stripped if strip_print is True")
    logger.info("Should be stripped")
    logging.debug("Should also be stripped")
    self.logger.warning("Stripped")
    x = 10
    return x
'''
    # Prune keeping critical_func intact, strip print
    pruned = prune_code_string(
        code, 
        critical_functions={"critical_func"}, 
        strip_logging=True, 
        strip_print=True,
        optimize_imports=False # keep import to test logging
    )
    
    assert "logger.info" not in pruned
    assert "logging.debug" not in pruned
    assert "self.logger.warning" not in pruned
    assert "print" not in pruned
    assert "x = 10" in pruned  # logic preserved

def test_prune_function_bodies():
    code = '''
def critical():
    return "critical"

def normal():
    return "normal"

class MyClass:
    def __init__(self, val):
        self.val = val
        
    def method(self):
        return self.val
'''
    # Default behavior: keep __init__, prune other non-critical
    pruned = prune_code_string(code, critical_functions={"critical"})
    
    # normal() and method() bodies should be replaced by ...
    assert "return 'normal'" not in pruned
    assert "return self.val" not in pruned
    assert "def normal():\n    ..." in pruned
    assert "def method(self):\n        ..." in pruned
    
    # critical() and __init__() bodies should be preserved
    assert "return 'critical'" in pruned
    assert "self.val = val" in pruned

def test_prune_function_bodies_prune_init():
    code = '''
class MyClass:
    def __init__(self, val):
        self.val = val
'''
    # Prune keeping __init__ disabled
    pruned = prune_code_string(code, keep_init=False)
    assert "self.val = val" not in pruned
    assert "def __init__(self, val):\n        ..." in pruned

def test_import_optimization():
    code = '''
import os
import sys
from collections import Counter, defaultdict
from math import *
import unused_module

def use_stuff():
    print(os.name)
    c = Counter()
'''
    # We keep use_stuff as critical to analyze references
    pruned = prune_code_string(code, critical_functions={"use_stuff"}, optimize_imports=True)
    
    # os is used in use_stuff
    assert "import os" in pruned
    
    # Counter is used in use_stuff, defaultdict is not
    assert "Counter" in pruned
    assert "defaultdict" not in pruned
    
    # sys and unused_module are completely unused
    assert "import sys" not in pruned
    assert "unused_module" not in pruned
    
    # Wildcard imports should be preserved
    assert "from math import *" in pruned
