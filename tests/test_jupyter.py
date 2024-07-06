import subprocess
import pytest
from helpers import refresh_testing_db


@refresh_testing_db
def test_jupyter():
    notebook_path = "tests/verifyCallMulitCallAndFetchAndSaveWorkInJupyter.ipynb"

    execute_command = ["jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace", notebook_path]

    result = subprocess.run(execute_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    clear_command = [
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--ClearOutputPreprocessor.enabled=True",
        "--inplace",
        notebook_path,
    ]

    subprocess.run(clear_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        # Print the outputs for debugging in the pytest output
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        # Use pytest to fail the test with an informative message
        pytest.fail("Notebook execution failed: {}".format(result.stderr))
