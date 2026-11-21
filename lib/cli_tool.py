import argparse
import shlex
import sys

from lib.models import Task, User


users = {}


class TaskManager:
    def __init__(self, user_store=None):
        self.users = users if user_store is None else user_store

    def add_task(self, args):
        user = self.users.get(args.user)
        if user is None:
            user = User(args.user)
            self.users[args.user] = user

        user.add_task(Task(args.title))

    def list_tasks(self, args):
        user = self.users.get(args.user)
        if user is None:
            print("❌ User not found.")
            return
        if not user.tasks:
            print(f"No tasks found for {user.name}.")
            return

        print(f"📋 Tasks for {user.name}:")
        for task in user.tasks:
            status = "x" if task.completed else " "
            print(f"[{status}] {task.title}")

    def complete_task(self, args):
        user = self.users.get(args.user)
        if user is None:
            print("❌ User not found.")
            return

        task = user.get_task_by_title(args.title)
        if task is None:
            print("❌ Task not found.")
            return

        task.complete()


manager = TaskManager()


def non_empty_argument(value):
    if not value.strip():
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def add_task(args):
    manager.add_task(args)


def list_tasks(args):
    manager.list_tasks(args)


def complete_task(args):
    manager.complete_task(args)


def create_parser():
    parser = argparse.ArgumentParser(description="Task Manager CLI")
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser(
        "add", aliases=["add-task"], help="Add a task for a user"
    )
    add_parser.add_argument("user", type=non_empty_argument, help="Name of the user")
    add_parser.add_argument("title", type=non_empty_argument, help="Title of the task")
    add_parser.set_defaults(func=manager.add_task)

    list_parser = subparsers.add_parser(
        "list", aliases=["list-tasks"], help="List a user's tasks"
    )
    list_parser.add_argument("user", type=non_empty_argument, help="Name of the user")
    list_parser.set_defaults(func=manager.list_tasks)

    complete_parser = subparsers.add_parser(
        "complete", aliases=["complete-task"], help="Complete a user's task"
    )
    complete_parser.add_argument(
        "user", type=non_empty_argument, help="Name of the user"
    )
    complete_parser.add_argument(
        "title", type=non_empty_argument, help="Title of the task"
    )
    complete_parser.set_defaults(func=manager.complete_task)

    return parser


def run_interactive(parser, input_fn=None):
    if input_fn is None:
        input_fn = input

    while True:
        try:
            line = input_fn("task-manager> ")
        except EOFError:
            print()
            return

        if line.strip() in {"exit", "quit"}:
            return
        if line.strip() in {"help", "?"}:
            parser.print_help()
            continue
        if not line.strip():
            continue

        try:
            command_args = shlex.split(line)
        except ValueError as error:
            print(f"❌ Invalid command: {error}")
            continue

        try:
            args = parser.parse_args(command_args)
        except SystemExit:
            continue

        if hasattr(args, "func"):
            args.func(args)


def main(argv=None):
    command_line = sys.argv[1:] if argv is None else argv
    parser = create_parser()
    if not command_line:
        run_interactive(parser)
        return

    args = parser.parse_args(command_line)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
