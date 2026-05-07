"""Master analyzer registry — discovers all schools/indicators/tools and runs them."""
from __future__ import annotations
import importlib
import pkgutil
from pathlib import Path
from typing import Callable
import pandas as pd
from ..engines.voting_engine import AnalyzerResult


def _discover(pkg_name: str) -> dict[str, Callable]:
    out: dict[str, Callable] = {}
    pkg = importlib.import_module(pkg_name)
    for mod_info in pkgutil.iter_modules(pkg.__path__):
        if mod_info.name.startswith("_"): continue
        mod = importlib.import_module(f"{pkg_name}.{mod_info.name}")
        if hasattr(mod, "analyze"):
            out[getattr(mod, "CODE", mod_info.name)] = mod.analyze
    return out


SCHOOLS = _discover("app.workers.analyzers.schools")
INDICATORS = _discover("app.workers.analyzers.indicators")
TOOLS = _discover("app.workers.analyzers.tools")


def run_all_schools(df: pd.DataFrame) -> list[AnalyzerResult]:
    return [fn(df) for fn in SCHOOLS.values()]

def run_all_indicators(df: pd.DataFrame) -> list[AnalyzerResult]:
    return [fn(df) for fn in INDICATORS.values()]

def run_all_tools(df: pd.DataFrame) -> list[AnalyzerResult]:
    return [fn(df) for fn in TOOLS.values()]
