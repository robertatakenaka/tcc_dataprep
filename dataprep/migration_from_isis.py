import argparse
import json

from datetime import datetime
from dataprep.utils import files_utils
from dataprep.preparation import migration_inputs


def adapt_data_paper(json_file_path, log_file_path, journals):
    """
    """
    print(json_file_path)
    data = migration_inputs.get_data_from_json_files(json_file_path)
    try:
        paper = migration_inputs.convert_paper(data, journals)
    except KeyError as e:
        print("Exception: %s" % e)
        print("Unable to convert data to register in RS: %s" % data)
        return
    else:
        files_utils.write_file(
            json_file_path + "_rs.json", json.dumps(paper)
        )


def adapt_data_papers(list_file_path, log_file_path, journals):
    """
    """
    files_utils.write_file(log_file_path, "", "w")
    with open(list_file_path) as fp:
        for row in fp.readlines():
            registered = adapt_data_paper(row.strip(), log_file_path, journals)
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

    adapt_data_paper_parser = subparsers.add_parser(
        "adapt_data_paper",
        help=(
            "Register a paper from document.json file. "
        )
    )
    adapt_data_paper_parser.add_argument(
        "source_file_path",
        help=(
            "/path/document.json"
        )
    )
    adapt_data_paper_parser.add_argument(
        "log_file_path",
        help=(
            "/path/registered.jsonl"
        )
    )
    adapt_data_paper_parser.add_argument(
        "subject_areas_file_path",
        help=(
            "/path/subject_areas.csv"
        )
    )
    ###################
    adapt_data_papers_parser = subparsers.add_parser(
        "adapt_data_papers",
        help=(
            "Register documents from a list of document.json file paths"
        )
    )
    adapt_data_papers_parser.add_argument(
        "list_file_path",
        help=(
            "/path/list.txt"
        )
    )
    adapt_data_papers_parser.add_argument(
        "log_file_path",
        help=(
            "/path/registered.jsonl"
        )
    )
    adapt_data_papers_parser.add_argument(
        "subject_areas_file_path",
        help=(
            "/path/subject_areas.csv"
        )
    )

    args = parser.parse_args()
    if args.command == "adapt_data_papers":
        journals = migration_inputs.read_subject_areas(
            args.subject_areas_file_path)
        adapt_data_papers(
            args.list_file_path,
            args.log_file_path,
            journals,
        )
    elif args.command == "adapt_data_paper":
        journals = migration_inputs.read_subject_areas(
            args.subject_areas_file_path)
        adapt_data_paper(
            args.source_file_path,
            args.log_file_path,
            journals,
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
