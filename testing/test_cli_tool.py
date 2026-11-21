import subprocess
import os
import sys
from types import SimpleNamespace

def run_cli_command(command):
    """Helper to run CLI command and capture output"""
    return subprocess.run(command, capture_output=True, text=True)

def test_add_task():
    result = run_cli_command(
        [sys.executable, "-m", "lib.cli_tool", "add-task", "Alice", "Submit report"]
    )
    assert "📌 Task 'Submit report' added to Alice." in result.stdout


def test_add_list_and_complete_commands(monkeypatch, capsys):
    from lib import cli_tool

    monkeypatch.setattr(cli_tool, "manager", cli_tool.TaskManager({}))
    for command in (
        ["task-manager", "add", "Alice", "Submit report"],
        ["task-manager", "list", "Alice"],
        ["task-manager", "complete", "Alice", "Submit report"],
        ["task-manager", "list", "Alice"],
    ):
        monkeypatch.setattr("sys.argv", command)
        cli_tool.main()

    output = capsys.readouterr().out
    assert "📌 Task 'Submit report' added to Alice." in output
    assert "📋 Tasks for Alice:\n[ ] Submit report" in output
    assert "✅ Task 'Submit report' completed." in output
    assert "[x] Submit report" in output


def test_interactive_session_keeps_tasks_in_memory(monkeypatch, capsys):
    from lib import cli_tool

    commands = iter(
        [
            'add-task Alice "Write unit tests"',
            "list Alice",
            'complete Alice "Write unit tests"',
            "list Alice",
            "exit",
        ]
    )
    monkeypatch.setattr(cli_tool, "manager", cli_tool.TaskManager({}))
    monkeypatch.setattr("builtins.input", lambda _prompt: next(commands))

    cli_tool.main([])

    output = capsys.readouterr().out
    assert "📋 Tasks for Alice:\n[ ] Write unit tests" in output
    assert "✅ Task 'Write unit tests' completed." in output
    assert "[x] Write unit tests" in output


def test_list_and_complete_report_missing_users_and_tasks(capsys):
    from lib.cli_tool import TaskManager
    from lib.models import User

    manager = TaskManager({})
    manager.users["Bob"] = User("Bob")
    manager.list_tasks(SimpleNamespace(user="Alice"))
    manager.complete_task(SimpleNamespace(user="Bob", title="Missing task"))

    assert capsys.readouterr().out.splitlines() == [
        "❌ User not found.",
        "❌ Task not found.",
    ]


def test_empty_title_is_rejected(capsys):
    from lib.cli_tool import create_parser

    parser = create_parser()
    try:
        parser.parse_args(["add", "Alice", "  "])
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("an empty task title should be rejected")

    assert "value must not be empty" in capsys.readouterr().err


def test_complete_task_with_script(tmp_path):
    """Runs everything in one subprocess so state is shared."""
    script_path = tmp_path / "script.py"
    script_content = f"""
import sys
sys.path.insert(0, '{os.getcwd().replace("\\\\", "/")}')

from lib.models import Task, User

users = {{}}
user = User("Bob")
users["Bob"] = user
task = Task("Finish lab")
user.add_task(task)
task.complete()
"""
    script_path.write_text(script_content)

    result = subprocess.run(
        [sys.executable, str(script_path)], capture_output=True, text=True
    )
    assert "✅ Task 'Finish lab' completed." in result.stdout
