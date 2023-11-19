#!/usr/bin/python3
from pathlib import Path

from .common import Access
from .operation.include_guards import IncludeGuard
from .operation.copyright import Copyright
from .operation.ifdef import IfDef


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
