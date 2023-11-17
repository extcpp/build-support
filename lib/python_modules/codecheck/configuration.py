#!/usr/bin/python3
from pathlib import Path

from .common import Access
from .include_guards import IncludeGuard
from .copyright import Copyright
from .ifdef import IfDef


class Configuration:
    def __init__(self, project_root: Path, check_only: bool = True, dirs=[], dirs_to_exclude=[]):
        access = Access.READ
        if check_only:
            access = Access.MODIFY

        self.project_root = project_root
        self.dirs = dirs
        self.dirs_to_exclude = dirs_to_exclude
        self.current_operation = None
        # create operations
        self.operations = []
        self.operations.append(IncludeGuard(access))
        self.operations.append(Copyright(access))
        self.operations.append(IfDef(access))
