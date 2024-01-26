import os
import subprocess

import pytest

filepaths = []
root_dir = os.getcwd()
for dirpath, dirnames, filenames in os.walk(root_dir):
    for filename in filenames:
        if (
            filename.endswith(".py")
            and not filename.endswith("__init__.py")
            and os.path.join(root_dir, filename) != __file__
        ):
            filepath_ = os.path.join(dirpath, filename)
            filepaths.append(filepath_)


@pytest.mark.parametrize("filepath", filepaths)
def test_all_docs(filepath: str):
    result = subprocess.run(["poetry", "run", "python", filepath])
    assert result.returncode == 0
