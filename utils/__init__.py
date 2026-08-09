"""Utils package for the Volta portfolio analysis scripts.

Public helpers live in ``utils.common`` (shared setup, banners, constants,
data-path resolution). The report-generation and PDF-processing submodules
(``utils.report_generator``, ``utils.pdf_processor``) are not eagerly imported
here — import them explicitly if needed, e.g. ``from utils.report_generator
import generate_funnel_excel``.
"""

from __future__ import annotations

from .common import CONSTANTS, data_path, print_section, print_subsection, setup

__all__ = [
    "CONSTANTS",
    "data_path",
    "print_section",
    "print_subsection",
    "setup",
]
