import pytest
from _pytest.mark import MarkDecorator, MarkInfo, Mark
from _pytest.skipping import MarkEvaluator
from datetime import datetime
import warnings


def pytest_configure(config):
    config.addinivalue_line("markers", "skip_until: Skips test until condition is met.")


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    skip_until_info = item.get_closest_marker('skip_until')
    if isinstance(skip_until_info, Mark):
        # If the date parameter is used, it will take precedence
        if "date" in skip_until_info.kwargs and isinstance(skip_until_info.kwargs["date"], datetime):
            skip_until_info.kwargs["condition"] = datetime.utcnow() >= skip_until_info.kwargs['date']
        eval_skip_until = MarkEvaluator(item, 'skip_until')
        skip_until_info.kwargs.get("condition", None)
        item._evalskipuntil = eval_skip_until
        if not eval_skip_until.istrue():
            pytest.skip(eval_skip_until.getexplanation())


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    evalskipuntil = getattr(item, '_evalskipuntil', None)
    if evalskipuntil is not None:
        if rep.skipped and type(rep.longrepr) is tuple:
            filename, line, reason = rep.longrepr
            filename, line = item.location[:2]
            rep.longrepr = filename, line, reason
        elif call.when == "call":
            filename, line, test = item.location
            warnings.warn_explicit('skip_until has expired. Please remove the skip_until', UserWarning, filename, line)


