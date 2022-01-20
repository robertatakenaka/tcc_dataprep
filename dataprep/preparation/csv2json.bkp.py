import argparse
import os
import json
import csv


# files = [
#     'references/references.csv',
#     'articles/articles.csv',
#     'articles/articles_langs.csv',
#     'data_with_lang/abstracts.csv',
#     'data_with_lang/article_titles.csv',
#     'data_with_lang/keywords.csv',
# ]

LABELS = dict(
    langs='articles_langs',
    abstracts='abstracts',
    keywords='keywords',
    article_titles='article_titles',
    references='references',
    articles='articles',
)


def get_fieldnames(file_path):
    with open(file_path, "r") as fp:
        for row in fp.readlines():
            print("get_fieldnames", row)
            try:
                return row.keys()
            except AttributeError:
                return row.strip().split(",")


def get_article_json_file_path(articles_json_folder_path, row):
    pid = row.get("pid") or row.get("key") or ''
    if len(pid) not in (23, 28):
        raise ValueError("pid is incorrect: %s" % row)

    year = pid[10:14]
    issn = pid[1:10]
    dirname = os.path.join(articles_json_folder_path, year, issn)

    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    return os.path.join(dirname, pid[:23])


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
    for k, v in LABELS.items():
        if k in filename:
            return v


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
            "%s does not match with none of %s" % (basename, LABELS.keys()))

    with open(input_csv_file_path, "r") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for row in reader:
            try:
                article_json_file_path = get_article_json_file_path(
                    output_articles_json_folder_path, row)
            except ValueError as e:
                print("")
                print(e)
                print("")
            else:
                add_article_data(article_json_file_path, data_label, row)


def main():
    parser = argparse.ArgumentParser(description='Group article data')
    subparsers = parser.add_subparsers(
        title='Command', metavar='', dest='command')

    merge_article_data_parser = subparsers.add_parser(
        'merge_article_data',
        help=("Lê arquivos vários `*.csv` que contém dados de um artigo"
              " e cria um único arquivo `<pid>.json` por artigo")
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
