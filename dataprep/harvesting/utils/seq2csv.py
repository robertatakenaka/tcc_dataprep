import csv
import os
from unicodedata import normalize

from html import unescape

# coleções temáticas que podem contribuir com repetições de registros
# por isso devem ser ignoradas
SKIP_COLLECTIONS = ["sss", "rve", "spa"]

FIELDS = "pid,collection,lang,text,original,pub_year".split(",")

SUBFIELDS = {
    "abstracts.seq": "a",
    "article_titles.seq": "t",
    "keywords.seq": "k",
    "title_mission.seq": "*",
}

LANGS = {}


def write_file(file_path, content, mode="w"):
    try:
        with open(file_path, mode) as fp:
            fp.write(content)
    except FileNotFoundError:
        os.makedirs(os.path.dirname(file_path))
        with open(file_path, mode) as fp:
            fp.write(content)


def entity_to_char(text):
    return unescape(text)


def seq2csv(seq_file_path, csv_file_path, fieldnames, fixer_func, sep):
    basename = os.path.basename(seq_file_path)
    fixer = fixer_func or format_text_and_lang
    fieldnames = fieldnames or ['pid', 'collection', 'lang', 'text']

    subfield = SUBFIELDS.get(basename) or "*"

    write_csv(read_seq_file(seq_file_path, sep=sep), fieldnames,
              csv_file_path, fixer, sep, subfield)


def read_seq_file(file_path, fieldnames=None, sep="|"):
    try:
        with open(file_path, "rb") as fp:
            for row in fp.readlines():
                row = row.decode("utf-8").strip()
                yield [item for item in row.split(sep)]
    except UnicodeDecodeError:

        with open(file_path, "r", encoding="iso-8859-1") as fp:
            for row in fp.readlines():
                try:
                    yield [item for item in row.strip().split(sep)]
                except Exception as e:
                    print("read_seq_file")
                    print(e)
                    print(row)


def write_csv(rows, fieldnames, output_file_path, fixer, sep, subfield=None):
    dirname = os.path.dirname(output_file_path)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

    write_file(output_file_path+".err", "")

    with open(output_file_path, 'w', newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            try:
                fixed = fixer(row, subfield, sep)
                if fixed['collection'] in SKIP_COLLECTIONS:
                    raise ValueError(f"Skip collection {fixed['collection']}")
            except ValueError:
                write_file(output_file_path+".err", str(row) + "\n", "a")
            else:
                if not fixed:
                    write_file(output_file_path+".err", str(row) + "\n", "a")
                    continue
                if fixer is format_key_and_value:
                    for item in fixed:
                        writer.writerow(item)
                else:
                    writer.writerow(fixed)


def clean_lang(raw_lang):
    chars = [
        c
        for c in entity_to_char(raw_lang or '')
        if c.isalpha()
    ]
    return "".join(chars).lower()


def format_references(row, subfield=None, sep=None):
    try:
        keys = [
            'pid',
            'pub_date', 'vol', 'num', 'page',
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

        d = {k: v for k, v in zip(keys, row)}
        d['pid'], d['collection'] = d['pid'].split("^c")
        d['num'], d['suppl'] = (d['num'] + "^s").split("^s")[:2]
        d['article_title'], __ = (d['article_title'] + "^l").split("^l")[:2]

        return d

    except ValueError as e:
        print(e)
        print(len(keys), len(row))
        print(keys)
        print(row)
        return {}


def format_articles(row, subfield=None, sep=None):
    # v880,'|',v881,'|',v35,'|',v65,'|',v31,'|',v32,'|',v131,v132,'|',v14,'|',v237,'|',replace(v702,'\','/'),'|',v71
    try:
        pid, aop_pid, issn, pub_date, vol, num, suppl, page, doi, path, doctopic = row
    except ValueError as e:
        print(e)
        print(row)
        return {}
    else:
        subfields = {}
        for item in page.split("^"):
            if item:
                subfields[item[0]] = item[1:]
        data = {
            "pid": pid,
            "aop_pid": aop_pid,
            "issn": issn,
            "pub_date": pub_date,
            "vol": vol,
            "num": num,
            "suppl": suppl,
            'fpage': subfields.get("f", ''), 'lpage': subfields.get("l", ''),
            'page_seq': subfields.get("s", ''),
            'elocation': subfields.get("e", ''),
            "doi": doi,
            "path": path,
            "doctopic": doctopic,
        }
        data['pid'], data['collection'] = data['pid'].split("^c")
        return data


def remove_extra_spaces(words):
    return " ".join([w.strip() for w in words.split(" ") if w])


def format_key_and_value(row, subfield=None, sep="|"):
    try:
        _id, _value = row
    except ValueError:
        if len(row) < 2:
            raise
        _id = row[0]
        _value = sep.join(row[1:])

    if "^c" not in _id:
        _id += "^c"
    _id, collection = _id.split("^c")
    _value = _value.replace("/", ";")
    items = [v for v in _value.split(";")]
    return [
        {
            "key": _id, "collection": collection,
            "value": standardize_keyword(item), "original": item,
        }
        for item in items
    ]


def _try_to_find_lang_in_text(_text, subfield):
    lang = None
    if subfield == "t" and "[title language=" in _text and "^l" not in _text:
        _text = _text[_text.find("[title language="):]
        _lang = _text[_text.find("=")+1:]
        lang_c = []
        for c in _lang:
            if c.isalpha():
                lang_c.append(c)
                if len(lang_c) == 2:
                    lang = "".join(lang_c)
                    break

        _text = _text[_text.find("]")+1:]

    if not _text.startswith("^"):
        _text = "^*" + _text

    if "^l" not in _text and lang:
        _text += "^l" + lang
    return _text


def format_text_and_lang(row, subfield, sep="|"):
    try:
        _pid, _text = row
    except ValueError:
        if len(row) < 2:
            raise
        _pid = row[0]
        _text = sep.join(row[1:])
    return _get_row_data(row, subfield, _pid, _text)


def format_text_and_lang_and_year(row, subfield, sep=None):
    try:
        _pid, _text, _year = row
    except ValueError:
        if len(row) < 3:
            raise
        _pid = row[0]
        _year = row[-1]
        _text = sep.join(row[1:-1])
    return _get_row_data(row, subfield, _pid, _text, _year)


def _get_row_data(row, subfield, _pid, _text, _year=None):
    try:
        pid, collection = _pid.split("^c")
    except ValueError:
        pid = _pid
        collection = ""

    if not pid or len(pid) != 23:
        raise ValueError("Invalid pid in {}".format(row))
    if not _text:
        raise ValueError("Not found text in {}".format(row))

    # remove "sujeiras" no campo do texto
    _text = _try_to_find_lang_in_text(_text, subfield)

    subfields = {}
    for item in _text.split("^"):
        if item:
            subfields[item[0]] = item[1:].strip()

    text = subfields.get(subfield) or subfields.get("*")
    if not text:
        raise ValueError("Not found text in {}".format(row))

    cleaned_text = standardize_text(text)

    lang = clean_lang(subfields.get("l"))

    if ' THE ' in cleaned_text and lang != 'en':
        print(pid, lang, cleaned_text[:10])
        lang = 'en'

    _year = _year or pid[10:14]

    return {
        "pid": pid, "collection": collection,
        "lang": lang, "text": cleaned_text,
        "original": text,
        "pub_year": _year
    }


def remove_diacritics(s):
    try:
        s = normalize('NFKD', s)
    except TypeError:
        s = normalize('NFKD', unicode(s, "utf-8"))
    finally:
        return s.encode('ASCII', 'ignore').decode('ASCII')


def standardize_keyword(txt):
    txt = entity_to_char(txt)
    txt = remove_extra_spaces(txt)
    txt = remove_diacritics(txt)
    txt = txt.upper()
    while txt and not txt[0].isalnum():
        txt = txt[1:]
    while txt and not txt[-1].isalnum():
        txt = txt[:-2]
    return txt


def standardize_text(txt):
    txt = entity_to_char(txt)
    return txt


def read_csv_file(file_path, fieldnames=None):
    fieldnames = fieldnames or FIELDS
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for row in reader:
            yield row


LANGS = {
    row['lang']: row['lang_text']
    for row in read_csv_file('dataprep/utils/LANGS.csv', ['lang_text', 'lang'])
}


def _get_journals_areas():
    journals_areas = {}
    for row in read_csv_file('dataprep/utils/journals_areas_pt.csv', ['issn_id', 'collection', 'subject_area']):
        issn_id = row['issn_id']
        journals_areas[issn_id] = journals_areas.get(issn_id) or []
        journals_areas[issn_id].append(row['subject_area'])
    print(journals_areas)
    return journals_areas


YEARS = [1900, 1940, 1980, 1990, 2000, 2005, 2010, 2015, 2020, 2025]


def _get_time_range(pub_year):

    pub_year = int(pub_year)
    prev = 1890
    for year in YEARS:
        if pub_year < year:
            return f'{prev}-{year}'
        prev = year


def _add_other_colums(new_row, row):
    new_row['lang_text'] = LANGS.get(row['lang'])
    new_row['issn_id'] = row['pid'][1:10]
    new_row['time_range'] = _get_time_range(row['pub_year'])
    return new_row


def prepare_abstracts_ds(input_file_path, output_file_path, selected_fieldnames):
    SUBJ_AREAS = _get_journals_areas()
    with open(output_file_path, newline='', mode="w") as csvfile:
        fieldnames = ['lang_text', 'issn_id', 'time_range', 'subject_area']
        fieldnames.extend(
            selected_fieldnames
        )
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in read_csv_file(input_file_path):
            try:
                if len(row['pid']) != 23:
                    raise ValueError
                if row['collection'] in SKIP_COLLECTIONS:
                    raise ValueError(f"Skip collection {row['collection']}")
                new_row = {
                    k: row[k]
                    for k in selected_fieldnames
                }
                new_row = _add_other_colums(new_row, row)
            except (KeyError, ValueError):
                continue
            else:
                try:
                    for sa in SUBJ_AREAS[new_row['issn_id']]:
                        new_row['subject_area'] = sa
                        writer.writerow(new_row)
                except KeyError as e:
                    new_row['subject_area'] = 'UNKNOWN'
                    writer.writerow(new_row)


def ent2char(text):
    return html.unescape(s)


def fix_htmlentities(input_file_path, output_file_path):
    dirname = os.path.dirname(output_file_path)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

    with open(output_file_path, 'w', encoding="utf-8") as fp:
        fp.write("")

    with open(input_file_path, "r") as fp:
        for row in fp.readlines():
            try:
                row = standardize_text(row)
            except:
                print(row)

            with open(output_file_path, 'a', encoding="utf-8") as fp:
                fp.write(row)


def fix_htmlentities_in_csv(input_file_path, output_file_path, origin, destination, fieldnames):
    dirname = os.path.dirname(output_file_path)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

    fieldnames = fieldnames.strip().split(",")
    print(fieldnames)

    with open(output_file_path, newline='', mode="w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in read_csv_file(input_file_path, fieldnames):
            try:
                row[destination] = standardize_text(row[origin])
            except:
                print(row)

            writer.writerow(row)
