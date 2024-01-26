import subprocess
from pathlib import Path

import pytest

filepaths = []
path = Path(__file__).parent
for p in path.rglob("*"):
    print(p.name)
for p in path.rglob("*"):
    if p.name.endswith(".py") and not p.name == "__init__.py" and p != Path(__file__):
        filepath_ = str(p.resolve())
        filepaths.append(filepath_)


@pytest.mark.parametrize("filepath", filepaths)
def test_all_docs(filepath: str):
    result = subprocess.run(["python", filepath])
    assert result.returncode == 0
