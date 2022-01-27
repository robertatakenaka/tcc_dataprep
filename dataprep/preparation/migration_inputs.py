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


# python /path/rs/app.py
RS_APP_CALL = os.getenv('RS_APP_CALL', default="python rs/app.py")


class NotFoundPartialJSONFileError(Exception):
    ...


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


def _get_pid_from_csv_row(row):
    """
    Retorna pid
    """
    pid = row.get("pid") or row.get('"pid"') or row.get("key") or ''
    if len(pid) not in (23, 28):
        raise ValueError("pid is incorrect: %s" % row)
    return pid


def _get_json_file_path_with_suffix(articles_json_folder_path, pid, suffix):
    """
    Retorna /folder_path/ISSN/YEAR/PID_<suffix>.json
    """
    article_json_file_path = get_article_json_file_path(
        articles_json_folder_path, pid[:23])
    return f"{article_json_file_path}_{suffix}.json"


def add_article_data(partial_json_file_path, data_label, row):
    print(partial_json_file_path)

    try:
        with open(partial_json_file_path, "r") as fp:
            content = fp.read()
    except IOError:
        data = {}
    else:
        data = json.loads(content)

    data[data_label] = data.get(data_label) or []
    if row not in data[data_label]:
        data[data_label].append(row)

        files_utils.write_file(partial_json_file_path, json.dumps(data))


def _get_data_label(filename):
    for k, v in LABELS_AND_FILENAME_SUFFIX.items():
        if k in filename:
            return v


def format_data(row):
    if row.get("original"):
        row['text'] = row['original']
        del row['original']
    return row


def csv_rows_to_json(input_csv_file_path, output_articles_json_folder_path):
    """
    Lê um arquivo CSV que contém um dos dados de artigo, por exemplo:
    references, langs, abstracts, ... e insere este dado no arquivo JSON
    do artigo correspondente
    """
    fieldnames = get_fieldnames(input_csv_file_path)
    basename = os.path.basename(input_csv_file_path)

    # abstracts, article_titles, keywords e references
    data_label = _get_data_label(basename)

    if not data_label:
        raise ValueError(
            "%s does not match with none of %s" %
            (basename, LABELS_AND_FILENAME_SUFFIX.keys()))

    with open(input_csv_file_path, "r") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for row in reader:
            try:
                pid = _get_pid_from_csv_row(row)
            except ValueError:
                continue
            partial_json_file_path = _get_json_file_path_with_suffix(
                output_articles_json_folder_path, pid, data_label)
            add_article_data(
                partial_json_file_path, data_label, format_data(row))


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


def convert_to_paper(data, journals):
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

    return dict(
        network_collection=data['collection'],
        pid=data['pid'],
        main_lang=data.get("lang"),
        doi=data.get("doi"),
        pub_year=data['pid'][10:14],
        uri='',
        subject_areas=list(set(subject_areas)),
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


def create_json_files_for_rs(input_csv_file_path, subject_areas_file_path,
                             output_articles_json_folder_path):
    """
    Lê um arquivo CSV que contém um PID de artigo e
    lê os arquivos JSON com dados parciais dos artigos
    (abstracts, article_titles, keywords, references)
    une em um só JSON com a estrutura esperada pelo RS
    """
    journals = read_subject_areas(subject_areas_file_path)

    fieldnames = get_fieldnames(input_csv_file_path)

    files_utils.write_file("exists.txt", "")
    files_utils.write_file("created.txt", "")
    files_utils.write_file("incomplete.txt", "")

    pids = get_pids_from_csv_file(input_csv_file_path)
    for pid in pids:

        rs_file_path = _get_json_file_path_with_suffix(
            output_articles_json_folder_path, pid, "rs")

        if os.path.isfile(rs_file_path):
            files_utils.write_file("exists.txt", pid + "\n", "a")

        try:
            data = get_data_from_partial_json_files(
                output_articles_json_folder_path, pid)
        except NotFoundPartialJSONFileError:
            files_utils.write_file("incomplete.txt", pid + "\n", "a")
        else:
            paper = convert_to_paper(data, journals)
            files_utils.write_file(
                rs_file_path, json.dumps(paper)
            )
            files_utils.write_file("created.txt", pid + "\n", "a")


def get_data_from_partial_json_files(output_articles_json_folder_path, pid):
    """
    Une os dados dos JSON abstracts, article_titles, keywords, references
    Raises
    ------
        NotFoundPartialJSONFileError
    Returns
    -------
        dict
    """
    data = {}
    for label, suffix in LABELS_AND_FILENAME_SUFFIX.items():
        try:
            file_path = _get_json_file_path_with_suffix(
                output_articles_json_folder_path, pid, suffix
            )
            print(file_path)
            data.update(json.loads(files_utils.read_file(file_path)))
        except:
            print("not found")
            raise NotFoundPartialJSONFileError(
                "Not found file %s for %s" % (suffix, pid))
    return data


def _split_list_in_n_lists(items, n=None):
    n = n or 4
    lists = [[] for i in range(n)]
    for i, item in enumerate(items):
        index = i % n
        try:
            lists[index].append(item)
        except (IndexError, AttributeError):
            lists[index] = [item]
    return lists


def get_pids_from_csv_file(input_csv_file_path):
    """
    Lê um arquivo CSV que contém PIDs
    """
    fieldnames = get_fieldnames(input_csv_file_path)
    print(fieldnames)
    pids = set()
    with open(input_csv_file_path, "r") as csvfile:
        for row in csv.DictReader(csvfile, fieldnames=fieldnames):
            try:
                pid = _get_pid_from_csv_row(row)
            except ValueError:
                continue
            else:
                pids.add(pid)
    return list(pids)


def pids_sorted_by_year(pids):
    return [
        pid
        for pid in sorted(pids, key=lambda pid: pid[10:14])
    ]


def _create_shell_scripts(json_files_lists, folder_path, filename_prefix, total):
    # create a shell script for each list
    cmds = []
    for i, json_files in enumerate(json_files_lists):

        name = f"{filename_prefix}_{i+1}_{len(json_files)}_{total}"

        sh_file_path = os.path.join(folder_path, f"{name}.sh")
        jsonl_file_path = os.path.join(folder_path, f"{name}.jsonl")
        out_file_path = os.path.join(folder_path, f"{name}.out")

        files_utils.write_file(sh_file_path, "")
        files_utils.write_file(jsonl_file_path, "")
        files_utils.write_file(out_file_path, "")

        cmds.append(f"chmod +x {sh_file_path};nohup {sh_file_path}>{out_file_path}&\n")

        for json_file in json_files:
            cmd = _get_rs_command(json_file, jsonl_file_path)
            files_utils.write_file(sh_file_path, cmd, "a")
    return cmds


def _shell_script_inputs(json_files_lists, folder_path, filename_prefix, total):
    """
    Create a file which contains a list of JSON file paths
    """
    lists_paths = []
    for i, json_files in enumerate(json_files_lists):

        name = f"{filename_prefix}_{i+1}_{len(json_files)}_{total}"

        input_file_path = os.path.join(folder_path, f"{name}.lst")

        files_utils.write_file(input_file_path, "\n".join(json_files))

        lists_paths.append(input_file_path)

    return lists_paths


def _create_shell_script(input_files_paths, sh_file_path):
    # create a shell script for the lists

    files_utils.write_file(sh_file_path, "")

    for input_file_path in input_files_paths:

        name, ext = os.path.splitext(input_file_path)
        result_jsonl_file_path = f"{name}.jsonl"
        out_file_path = f"{name}.out"

        files_utils.write_file(result_jsonl_file_path, "")
        files_utils.write_file(out_file_path, "")

        cmd = (
            f"nohup {RS_APP_CALL} register_new_papers "
            f"{input_file_path} {result_jsonl_file_path}>{out_file_path}&\n"
        )
        files_utils.write_file(sh_file_path, cmd, "a")


def create_register_papers_sh(
        pid_csv_file_path, articles_json_folder_path,
        outs_folder_path, main_shell_script_path,
        list_filename_prefix=None,
        n_calls=None):

    # le os pids de um arquivo csv
    pids = get_pids_from_csv_file(pid_csv_file_path)
    print(len(pids))

    # ordena por ano
    sorted_by_year = pids_sorted_by_year(pids)

    # obtém a lista de jsons
    json_file_paths = [
        _get_json_file_path_with_suffix(articles_json_folder_path, pid, "rs")
        for pid in sorted_by_year
    ]

    # separa em grupos
    json_files_lists = _split_list_in_n_lists(json_file_paths, n_calls or 4)
    prefix = (
        list_filename_prefix or
        os.path.splitext(os.path.basename(pid_csv_file_path))[0]
    )
    input_files_paths = _shell_script_inputs(
        json_files_lists, outs_folder_path, prefix, len(json_file_paths)
    )
    _create_shell_script(input_files_paths, main_shell_script_path)
    return {
        "shell script": main_shell_script_path,
        "outs path": outs_folder_path,
    }


def main():
    parser = argparse.ArgumentParser(description="Migration tool")
    subparsers = parser.add_subparsers(title="Commands", metavar="", dest="command")

    csv_rows_to_json_parser = subparsers.add_parser(
        'csv_rows_to_json',
        help=("Lê arquivo `*.csv` que contém dados de um artigo"
              " e cria um JSON correspondente")
    )
    csv_rows_to_json_parser.add_argument(
        'input_csv_file_path',
        help='input_csv_file_path'
    )
    csv_rows_to_json_parser.add_argument(
        'output_folder_path',
        help='output_folder_path'
    )

    create_json_files_for_rs_parser = subparsers.add_parser(
        'create_json_files_for_rs',
        help=("Lê arquivo `*.csv` que contém pids"
              " e junta os arquivos JSON parciais e gera um único")
    )
    create_json_files_for_rs_parser.add_argument(
        'input_csv_file_path',
        help='input_csv_file_path'
    )
    create_json_files_for_rs_parser.add_argument(
        "subject_areas_file_path",
        help=(
            "/path/subject_areas.csv"
        )
    )
    create_json_files_for_rs_parser.add_argument(
        'output_folder_path',
        help='output_folder_path'
    )

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
        "--filename_prefix",
        help=("Prefix for filename that contains the splitted list of pids")
    )
    create_register_papers_sh_parser.add_argument(
        "--simultaneous_calls",
        default=4,
        help=("Number of simultaneous calls")
    )

    args = parser.parse_args()
    if args.command == "create_register_papers_sh":
        ret = create_register_papers_sh(
            args.pid_csv_file_path,
            args.articles_json_folder_path,
            args.lists_folder_path,
            args.shell_script_file_path,
            args.filename_prefix,
            int(args.simultaneous_calls or 4),
        )
        print(ret)
    elif args.command == 'csv_rows_to_json':
        csv_rows_to_json(
            args.input_csv_file_path, args.output_folder_path)
    elif args.command == 'create_json_files_for_rs':
        create_json_files_for_rs(
            args.input_csv_file_path,
            args.subject_areas_file_path,
            args.output_folder_path)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
