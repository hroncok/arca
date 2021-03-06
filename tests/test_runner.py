import json
import tempfile
from pathlib import Path

import pytest

import arca._runner as runner
from arca import Task, Result


@pytest.mark.parametrize("definition", [
    "asdfasdf asdf",
    "{asdf: 12",
    {"entry_point": ["library.mod", "func"]},
    {"entry_point": {}},
    {"entry_point": {"module_name": "library.mod"}},
    {"entry_point": {"module_name": "library.mod", "object_name": "func"}},
    {"entry_point": {"module_name": "library.mod", "object_name": "func"},
     "args": None},
    {"entry_point": {"module_name": "library.mod", "object_name": "func"},
     "args": None,
     "kwargs": None},
    {"entry_point": {"module_name": "library.mod", "object_name": "func"},
     "args": {"eh": 1},
     "kwargs": {}},
    {"entry_point": {"module_name": "library.mod", "object_name": "func"},
     "args": {"eh": 1},
     "kwargs": None},
    {"entry_point": {"module_name": "library.mod", "object_name": "func"},
     "args": [1, 2, 3],
     "kwargs": None},
    {"entry_point": {"module_name": "library.mod", "object_name": "func"},
     "args": [1, 2, 3],
     "kwargs": [1, 2, 3]},
])
def test_definition_corruption(definition):
    _, file = tempfile.mkstemp()
    file = Path(file)

    if isinstance(definition, dict):
        file.write_text(json.dumps(definition))
    else:
        file.write_text(definition)

    output = runner.run(str(file))
    assert isinstance(output, dict)
    assert not output["success"]
    assert output["error"]
    assert output["reason"] == "corrupted_definition"

    file.unlink()


@pytest.mark.parametrize("module_name,object_name", [
    ("library", "func"),
    ("library.mod", "func"),
    ("arca", "SomeRandomClass"),
    ("arca", "Arca.some_random_method"),
])
def test_import_error(module_name, object_name):
    _, file = tempfile.mkstemp()
    file = Path(file)

    file.write_text(json.dumps({
        "entry_point": {"module_name": module_name, "object_name": object_name},
        "args": [1, 2, 3],
        "kwargs": {"x": 4, "y": 5}
    }))

    output = runner.run(str(file))
    assert isinstance(output, dict)
    assert not output["success"]
    assert output["error"]
    assert output["reason"] == "import"

    file.unlink()


@pytest.mark.parametrize("func,result", [
    (lambda *args, **kwargs: sum(args) + kwargs["x"] + kwargs["y"], True),
    (lambda: 15, TypeError),
    (lambda *args, **kwargs: 10 / 0, ZeroDivisionError)
])
def test_run(mocker, func, result):
    load = mocker.patch("arca._runner.EntryPoint.load")
    load.return_value = func

    _, file = tempfile.mkstemp()
    file = Path(file)

    file.write_text(json.dumps({
        "entry_point": {"module_name": "library.mod", "object_name": "sum"},
        "args": [1, 2, 3],
        "kwargs": {"x": 4, "y": 5}
    }))

    output = runner.run(str(file))
    assert isinstance(output, dict)
    if result is True:
        assert output["success"] is True
        assert output["result"] == 15
    else:
        assert output["success"] is False
        assert result.__name__ in output["error"]

    file.unlink()


@pytest.mark.parametrize("args,kwargs,result", [
    ([2], None, 4),
    (None, {"カ": 2}, 4),
    (["片仮名"], None, "片仮名片仮名"),
    (None, {"カ": "片仮名"}, "片仮名片仮名"),
])
def test_unicode(mocker, args, kwargs, result):
    load = mocker.patch("arca._runner.EntryPoint.load")

    def func(カ):
        return カ * 2

    load.return_value = func

    _, file = tempfile.mkstemp()
    file = Path(file)

    file.write_text(Task("library.mod:func", args=args, kwargs=kwargs).json)

    output = runner.run(str(file))

    assert Result(output).output == result

    file.unlink()
