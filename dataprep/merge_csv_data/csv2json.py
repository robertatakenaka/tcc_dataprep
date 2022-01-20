import argparse
import os
import json
import csv


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


def main():
    parser = argparse.ArgumentParser(description='Group article data')
    subparsers = parser.add_subparsers(
        title='Command', metavar='', dest='command')

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

    if args.command == 'merge_article_data':
        merge_article_data(args.input_csv_file_path, args.output_folder_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
