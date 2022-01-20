import logging
import argparse
import json
import csv
import os
from datetime import datetime

from dataprep.utils import files_utils


LABELS_AND_FILENAME_SUFFIX = dict(
    abstracts='abstracts',
    keywords='keywords',
    article_titles='article_titles',
    references='references',
)


def get_fieldnames(file_path):
    with open(file_path, "r") as fp:
        for row in fp.readlines():
            try:
                return row.keys()
            except AttributeError:
                print("get_fieldnames", row)
                return row.strip().split(",")


def get_article_json_file_path(folder_path, pid):
    """
    Retorna /folder_path/ISSN/YEAR/PID
    """
    return os.path.join(folder_path, pid[1:10], pid[10:14], pid)


def _get_article_json_file_path(articles_json_folder_path, data_label, row):
    """
    Retorna /folder_path/ISSN/YEAR/PID_<data_label>.json
    """
    pid = row.get("pid") or row.get("key") or ''
    if len(pid) not in (23, 28):
        raise ValueError("pid is incorrect: %s" % row)

    article_json_file_path = get_article_json_file_path(
        articles_json_folder_path, pid[:23])
    dirname = os.path.dirname(article_json_file_path)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    return f"{article_json_file_path}_{data_label}.json"


def add_article_data(article_json_file_path, data_label, row):
    print(article_json_file_path)

    try:
        with open(article_json_file_path, "r") as fp:
            content = fp.read()
    except IOError:
        content = "{}"

    data = json.loads(content)
    data[data_label] = data.get(data_label) or []

    if row not in data[data_label]:
        data[data_label].append(row)
        with open(article_json_file_path, "w") as fp:
            fp.write(json.dumps(data))


def _get_data_label(filename):
    for k, v in LABELS_AND_FILENAME_SUFFIX.items():
        if k in filename:
            return v


def format_data(row):
    if row.get("original"):
        row['text'] = row['original']
        del row['original']
    return row


def merge_article_data(input_csv_file_path, output_articles_json_folder_path):
    """
    Lê um arquivo CSV que contém um dos dados de artigo, por exemplo:
    references, langs, abstracts, ... e insere este dado no arquivo JSON
    do artigo correspondente
    """
    if not os.path.isdir(output_articles_json_folder_path):
        os.makedirs(output_articles_json_folder_path)

    fieldnames = get_fieldnames(input_csv_file_path)
    basename = os.path.basename(input_csv_file_path)
    data_label = _get_data_label(basename)
    if not data_label:
        raise ValueError(
            "%s does not match with none of %s" % (basename, LABELS_AND_FILENAME_SUFFIX.keys()))

    with open(input_csv_file_path, "r") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for row in reader:
            try:
                article_json_file_path = _get_article_json_file_path(
                    output_articles_json_folder_path, data_label, row)
            except ValueError as e:
                print("")
                print(e)
                print("")
            else:
                add_article_data(article_json_file_path, data_label, format_data(row))


expected_reference_attributes = (
    'pub_year', 'vol', 'num', 'suppl', 'page',
    'surname', 'organization_author', 'doi', 'journal',
    'paper_title', 'source', 'issn', 'thesis_date',
    'thesis_loc', 'thesis_country', 'thesis_degree', 'thesis_org',
    'conf_date', 'conf_loc', 'conf_country', 'conf_name', 'conf_org',
    'publisher_loc', 'publisher_country', 'publisher_name', 'edition',
    'source_person_author_surname', 'source_organization_author',
)


def fix_csv_ref_attributes(reference_from_csv_file):
    """
    {"surname": "Paterson",
    "conf_org": "",
    "vol": "34",
    "conf_name": "",
    "pid": "S0011-8516202100010001000003",
    "source_author": "",
    "thesis_org": "",
    "num": "52",
    "thesis_degree": "",
    "publisher_country": "",
    "publisher_name": "",
    "article_title": "Vaccine hesitancy and healthcare providers",
    "suppl": "",
    "source": "",
    "thesis_date": "",
    "publisher_loc": "",
    "journal": "Vaccine",
    "thesis_loc": "",
    "collection": "sza",
    "corpauth": "",
    "conf_loc": "",
    "pub_date": "20160000",
    "thesis_country": "",
    "doi": "",
    "edition": "",
    "issn": "0264-410X",
    "conf_date": "",
    "conf_country": "",
    "page": "6700-6",
    "source_corpauth": ""}
    """
    ref = {}
    for k in expected_reference_attributes:
        value = (reference_from_csv_file.get(k) or '').strip()
        ref[k] = value.split("^")[0]

    ref['pub_year'] = (reference_from_csv_file.get("pub_date") or '')[:4]
    ref['organization_author'] = (reference_from_csv_file.get("corpauth") or '').split("^")[0]
    ref['source_organization_author'] = (reference_from_csv_file.get("source_corpauth") or '').split("^")[0]
    ref['source_person_author_surname'] = (reference_from_csv_file.get("source_author") or '').split("^")[0]
    ref['paper_title'] = (reference_from_csv_file.get("article_title") or '').split("^")[0]
    ref['source'] = (ref['source'] or '').split("^")[0]
    ref['paper_title'] = (ref['paper_title'].strip() or '').split("^")[0] or None
    return ref


def convert_paper(data, journals):
    paper_titles = []
    for item in data.get("article_titles") or []:
        paper_titles.append({"lang": item["lang"], "text": item["text"]})

    abstracts = []
    for item in data.get("abstracts") or []:
        abstracts.append({"lang": item["lang"], "text": item["text"]})

    keywords = []
    for item in data.get("keywords") or []:
        keywords.append({"lang": item["lang"], "text": item["text"]})

    references = []
    for ref in data.get("references") or []:
        references.append(fix_csv_ref_attributes(ref))

    subject_areas = data.get("subject_areas") or []
    if not subject_areas:
        j = journals.get(data['pid'][1:10])
        if j:
            subject_areas = j

    if not data.get("collection") or not data.get("pid"):
        for k in ("abstracts", "keywords", "article_titles"):
            items = data.get(k)
            if not items:
                continue
            try:
                data['pid'] = items[0]['pid']
                data['collection'] = items[0]['collection']
            except KeyError:
                pass
            else:
                break
    return dict(
        network_collection=data['collection'],
        pid=data['pid'],
        main_lang=data.get("lang"),
        doi=data.get("doi"),
        pub_year=data['pid'][10:14],
        subject_areas=set(subject_areas),
        paper_titles=paper_titles,
        abstracts=abstracts,
        keywords=keywords,
        references=references,
    )


def read_subject_areas(file_path):
    journals = {}

    with open(file_path) as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            issn = row['key']
            journals[issn] = journals.get(issn) or set()
            journals[issn].add(row['value'])

    return journals


def complete_data(data, json_file_path):
    for label, suffix in LABELS_AND_FILENAME_SUFFIX.items():
        if not data.get(label):
            file_path = json_file_path + f"_{suffix}.json"
            if os.path.isfile(file_path):
                data.update(json.loads(files_utils.read_file(file_path)))


def _split_list_in_n_lists(items, n=None):
    n = n or 4
    lists = [[] for i in range(n)]
    for i, item in enumerate(items):
        index = i % n
        try:
            lists[index].append(item)
        except (IndexError, AttributeError):
            lists[index] = [item]
    print(f"Created {n} lists")
    print([len(l) for l in lists])
    return lists


def _get_article_json_file_paths(pid_csv_file_path, articles_json_folder_path):
    pids = [
        row['pid'] for row in files_utils.read_csv_file(pid_csv_file_path)
    ]
    return [
        get_article_json_file_path(articles_json_folder_path, pid)
        for pid in sorted(pids, key=lambda pid: pid[10:14])
    ]


def _save_lists(lists, folder_path, filename_prefix, total):
    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)

    # create the a list file for each call
    files_paths = []
    for i, list_rows in enumerate(lists):
        file_path = os.path.join(
            folder_path,
            f"{filename_prefix}_{i+1}_{len(list_rows)}_{total}.txt",
        )
        files_paths.append(file_path)
        files_utils.write_file(file_path, "\n".join(list_rows), "w")
    return files_paths


def _get_register_papers_command(
        articles_json_files_list_file_path,
        subject_areas_journals_csv_file_path,
        ):
    outputs_path = os.path.dirname(articles_json_files_list_file_path)
    basename = os.path.splitext(
        os.path.basename(articles_json_files_list_file_path))[0]
    print(basename)

    output_jsonl_file_path = os.path.join(outputs_path, basename+".jsonl")
    nohup_out_file_path = os.path.join(outputs_path, basename+".out")

    # migration_from_isis must be registered as console_scripts entry_points in
    # setup.py
    return (
        "nohup migration_from_isis register_papers "
        f"{articles_json_files_list_file_path} {output_jsonl_file_path} "
        f"{subject_areas_journals_csv_file_path} "
        f" --create_sources --create_links>{nohup_out_file_path}&"
    )


def create_register_papers_sh(
        pid_csv_file_path, articles_json_folder_path,
        subject_areas_journals_csv_file_path,
        lists_folder_path, shell_script_path,
        list_filename_prefix=None,
        n_calls=None):

    json_file_paths = _get_article_json_file_paths(
        pid_csv_file_path, articles_json_folder_path,
    )
    lists = _split_list_in_n_lists(json_file_paths, n_calls or 4)
    prefix = (
        list_filename_prefix or
        os.path.splitext(os.path.basename(pid_csv_file_path))[0]
    )
    input_file_paths = _save_lists(
        lists, lists_folder_path, prefix, len(json_file_paths),
    )

    with open(shell_script_path, "w") as fp:
        for input_file_path in input_file_paths:
            command = _get_register_papers_command(
                input_file_path,
                subject_areas_journals_csv_file_path,
            )
            fp.write(f"{command}\n")
    return {
        "shell script": shell_script_path,
        "lists": input_file_paths,
    }


def main():
    parser = argparse.ArgumentParser(description="Migration tool")
    subparsers = parser.add_subparsers(title="Commands", metavar="", dest="command")

    create_register_papers_sh_parser = subparsers.add_parser(
        "create_register_papers_sh",
        help=(
            "Create shell script to call rs simultaneously"
        )
    )
    create_register_papers_sh_parser.add_argument(
        "pid_csv_file_path",
        help=(
            "/path/pid.csv"
        )
    )
    create_register_papers_sh_parser.add_argument(
        "articles_json_folder_path",
        help=(
            "Location of JSON files with article data: "
            "/path/articles_json_folder"
        )
    )
    create_register_papers_sh_parser.add_argument(
        "subject_areas_file_path",
        help=(
            "/path/subject_areas.csv"
        )
    )
    create_register_papers_sh_parser.add_argument(
        "lists_folder_path",
        help=(
            "/path/lists_folder"
        )
    )
    create_register_papers_sh_parser.add_argument(
        "shell_script_file_path",
        help=(
            "Shell script to run/path/run_rs.sh"
        )
    )
    create_register_papers_sh_parser.add_argument(
        "--list_filename_prefix",
        help=("Prefix for filename that contains the splitted list of pids")
    )
    create_register_papers_sh_parser.add_argument(
        "--simultaneous_calls",
        default=4,
        help=("Number of simultaneous call")
    )

    merge_article_data_parser = subparsers.add_parser(
        'merge_article_data',
        help=("Lê arquivo `*.csv` que contém dados de um artigo"
              " e cria um JSON correspondente")
    )
    merge_article_data_parser.add_argument(
        'input_csv_file_path',
        help='input_csv_file_path'
    )
    merge_article_data_parser.add_argument(
        'output_folder_path',
        help='output_folder_path'
    )

    args = parser.parse_args()
    if args.command == "create_register_papers_sh":
        ret = create_register_papers_sh(
            args.pid_csv_file_path,
            args.articles_json_folder_path,
            args.subject_areas_file_path,
            args.lists_folder_path,
            args.shell_script_file_path,
            args.list_filename_prefix,
            args.simultaneous_calls,
        )
        print(ret)
    elif args.command == 'merge_article_data':
        merge_article_data(args.input_csv_file_path, args.output_folder_path)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
