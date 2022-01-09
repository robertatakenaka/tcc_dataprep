import argparse
import os
import json
import csv


files = [
    'references/references.csv',
    'articles/articles.csv',
    'articles/articles_langs.csv',
    'data_with_lang/abstracts.csv',
    'data_with_lang/article_titles.csv',
    'data_with_lang/keywords.csv',
]


def get_fieldnames(file_path):
    with open(file_path, "r") as fp:
        for row in fp.readlines():
            print("get_fieldnames", row)
            try:
                return row.keys()
            except AttributeError:
                return row.strip().split(",")


def add_article_data(output_folder_path, key, row):
    id = row.get("pid") or row.get("key")
    subdir1 = id[10:14]
    subdir2 = id[1:10]
    dirname = os.path.join(output_folder_path, subdir1, subdir2)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    file_path = os.path.join(dirname, id[:23])
    print(file_path)
    content = "{}"
    try:
        with open(file_path, "r") as fp:
            content = fp.read()
    except IOError:
        data = {}
    else:
        data = json.loads(content)

    data[key] = data.get(key) or []

    with open(file_path, "w") as fp:
        data[key].append(row)
        fp.write(json.dumps(data))


def merge_article_data(input_file_path, output_folder_path):
    if not os.path.isdir(output_folder_path):
        os.makedirs(output_folder_path)

    fieldnames = get_fieldnames(input_file_path)
    basename = os.path.basename(input_file_path)
    name, ext = os.path.splitext(basename)
    with open(input_file_path, "r") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for row in reader:
            add_article_data(output_folder_path, name, row)


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
