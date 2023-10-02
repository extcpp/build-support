#!/usr/bin/python3
from pathlib import Path
import obi.util.logging as olog

logger = olog.init_logging(Path(__name__).stem)
olog.apply_formatter(logger, olog.create_obi_formatter_short())
