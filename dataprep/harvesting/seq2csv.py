import argparse

from dataprep.harvesting.utils import seq2csv


def main():
    parser = argparse.ArgumentParser(description='Data collector')
    subparsers = parser.add_subparsers(
        title='Command', metavar='', dest='command')

    # regular_parser = subparsers.add_parser(
    #     'seq2csv',
    #     help=("Converte `*.seq` para `*.csv`")
    # )
    # regular_parser.add_argument(
    #     'seq_file_path',
    #     help='seq_file_path'
    # )
    # regular_parser.add_argument(
    #     'csv_file_path',
    #     help='csv_file_path'
    # )

    text_and_lang_parser = subparsers.add_parser(
        'text_and_lang',
        help=("Converte `text_and_lang.seq` para `text_and_lang.csv`")
    )
    text_and_lang_parser.add_argument(
        'seq_file_path',
        help='seq_file_path'
    )
    text_and_lang_parser.add_argument(
        'csv_file_path',
        help='csv_file_path'
    )

    key_and_value_parser = subparsers.add_parser(
        'key_and_value',
        help=("Converte `key_and_value.seq` para `key_and_value.csv`")
    )
    key_and_value_parser.add_argument(
        'seq_file_path',
        help='seq_file_path'
    )
    key_and_value_parser.add_argument(
        'csv_file_path',
        help='csv_file_path'
    )

    articles_parser = subparsers.add_parser(
        'articles',
        help=("Converte `articles.seq` para `articles.csv`")
    )
    articles_parser.add_argument(
        'seq_file_path',
        help='seq_file_path'
    )
    articles_parser.add_argument(
        'csv_file_path',
        help='csv_file_path'
    )

    references_parser = subparsers.add_parser(
        'references',
        help=("Converte `references.seq` para `references.csv`")
    )
    references_parser.add_argument(
        'seq_file_path',
        help='seq_file_path'
    )
    references_parser.add_argument(
        'csv_file_path',
        help='csv_file_path'
    )

    args = parser.parse_args()

    func = None
    fieldnames = None
    if args.command == 'text_and_lang':
        func = seq2csv.format_text_and_lang
        fieldnames = ['pid', 'collection', 'lang', 'text', "original"]
    elif args.command == 'key_and_value':
        func = seq2csv.format_key_and_value
        fieldnames = ['key', 'collection', 'value', "original"]
    elif args.command == 'authors':
        func = seq2csv.format_authors
        fieldnames = ['key', 'collection', 'surname', 'given_names', 'orcid']
    elif args.command == 'references':
        func = seq2csv.format_references
        fieldnames = [
            'pid', 'collection',
            'pub_date', 'vol', 'num', 'suppl', 'page',
            'surname', 'corpauth',
            'doi', 'journal',
            'article_title',
            'source',
            'issn',
            'thesis_date', 'thesis_loc', 'thesis_country', 'thesis_degree',
            'thesis_org',
            'conf_date', 'conf_loc', 'conf_country', 'conf_name', 'conf_org',
            'publisher_loc', 'publisher_country', 'publisher_name', 'edition',
            'source_author', 'source_corpauth',
        ]
    elif args.command == 'articles':
        func = seq2csv.format_articles
        fieldnames = ['pid', 'collection', 'aop_pid', 'issn', 'pub_date',
                      'vol', 'num', 'suppl',
                      'fpage', 'lpage', 'page_seq', 'elocation',
                      'doi', 'path', 'doctopic']
    else:
        parser.print_help()

    if fieldnames and func and args.command:
        seq2csv.seq2csv(
            args.seq_file_path, args.csv_file_path, fieldnames, func)


if __name__ == "__main__":
    main()
