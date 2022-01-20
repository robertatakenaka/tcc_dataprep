import argparse
import json

from datetime import datetime
from rs import (
    app,
)
from dataprep.utils import files_utils
from dataprep.preparation import migration_inputs


def register_paper(json_file_path, log_file_path, journals, create_sources=False ,create_links=False):
    """
    """
    print(json_file_path)
    try:
        content = files_utils.read_file(json_file_path)
        data = json.loads(content)
    except IOError as e:
        data = {}
    except Exception as e:
        print("Unable to process %s: %s" % (json_file_path, e))
        return
    data = migration_inputs.complete_data(data)
    try:
        paper = migration_inputs.convert_paper(data, journals)
    except KeyError as e:
        print("Unable to convert data to register in RS %s: %s" % (data, e))
        return
    paper['create_sources'] = create_sources
    paper['create_links'] = create_links
    return app.receive_new_paper(**paper)


def register_papers(list_file_path, log_file_path, journals, create_sources, create_links):
    """
    """
    files_utils.write_file(log_file_path, "", "w")
    with open(list_file_path) as fp:
        for row in fp.readlines():
            registered = register_paper(row.strip(), log_file_path, journals,
                                        create_sources, create_links)
            if not registered:
                continue
            # registered['file_path'] = row.strip()
            # if registered.get("registered_paper"):
            #     registered['registered_paper'] = registered.get("registered_paper").pid
            # for k in ('recommended', 'rejected', 'selected_ids'):
            #     if registered.get(k):
            #         registered[k] = len(registered[k])
            registered['datetime'] = datetime.now().isoformat()
            content = json.dumps(registered)
            files_utils.write_file(log_file_path, content + "\n", "a")


def main():
    parser = argparse.ArgumentParser(description="Migration tool")
    subparsers = parser.add_subparsers(title="Commands", metavar="", dest="command")

    register_paper_parser = subparsers.add_parser(
        "register_paper",
        help=(
            "Register a paper from document.json file. "
        )
    )
    register_paper_parser.add_argument(
        "source_file_path",
        help=(
            "/path/document.json"
        )
    )
    register_paper_parser.add_argument(
        "log_file_path",
        help=(
            "/path/registered.jsonl"
        )
    )
    register_paper_parser.add_argument(
        "subject_areas_file_path",
        help=(
            "/path/subject_areas.csv"
        )
    )

    register_papers_parser = subparsers.add_parser(
        "register_papers",
        help=(
            "Register documents from a list of document.json file paths"
        )
    )
    register_papers_parser.add_argument(
        "list_file_path",
        help=(
            "/path/list.txt"
        )
    )
    register_papers_parser.add_argument(
        "log_file_path",
        help=(
            "/path/registered.jsonl"
        )
    )
    register_papers_parser.add_argument(
        "subject_areas_file_path",
        help=(
            "/path/subject_areas.csv"
        )
    )
    register_papers_parser.add_argument(
        "--create_sources",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "/path/subject_areas.csv"
        )
    )
    register_papers_parser.add_argument(
        "--create_links",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "/path/subject_areas.csv"
        )
    )

    args = parser.parse_args()
    if args.command == "register_papers":
        journals = migration_inputs.read_subject_areas(
            args.subject_areas_file_path)
        register_papers(
            args.list_file_path,
            args.log_file_path,
            journals,
            args.create_sources,
            args.create_links,
        )
    elif args.command == "register_paper":
        journals = migration_inputs.read_subject_areas(
            args.subject_areas_file_path)
        register_paper(
            args.source_file_path,
            args.log_file_path,
            journals
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
