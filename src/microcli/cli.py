import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="microcli",
        description="microcli CLI - Bootstrap and learn microcli microapps",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # new subcommand
    new_parser = subparsers.add_parser("new", help="Create a new microapp")
    new_parser.add_argument(
        "--name",
        required=True,
        help="Name of the microapp (becomes <name>.py)",
    )
    new_parser.add_argument(
        "--title",
        required=True,
        help="Title/description for the microapp",
    )
    new_parser.add_argument(
        "--commands",
        required=True,
        help="Comma-separated list of commands (e.g., create,list,delete)",
    )

    subparsers.add_parser("learn", help="Learn about microcli framework")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == "new":
        print(f"new command: name={args.name}, title={args.title}, commands={args.commands}")
    elif args.command == "learn":
        print("learn command placeholder")


if __name__ == "__main__":
    main()
