import csv
import os
from unicodedata import normalize

from html import unescape


SUBFIELDS = {
    "abstracts.seq": "a",
    "article_titles.seq": "t",
    "keywords.seq": "k",
    "title_mission.seq": "*",
}


def entity_to_char(text):
    return unescape(text)


def seq2csv(seq_file_path, csv_file_path, fieldnames, fixer_func, sep):
    basename = os.path.basename(seq_file_path)
    fixer = fixer_func or format_text_and_lang
    fieldnames = fieldnames or ['pid', 'collection', 'lang', 'text']

    subfield = SUBFIELDS.get(basename) or "*"

    write_csv(read_seq_file(seq_file_path, sep=sep), fieldnames,
              csv_file_path, fixer, subfield)


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


def write_csv(rows, fieldnames, output_file_path, fixer, subfield=None):
    dirname = os.path.dirname(output_file_path)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    with open(output_file_path, 'w', newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            fixed = fixer(row, subfield)
            if not fixed:
                continue
            if fixer is format_key_and_value:
                for item in fixed:
                    writer.writerow(item)
            else:
                writer.writerow(fixed)


def format_lang(raw_lang):
    chars = [
        c.lower()
        for c in entity_to_char(raw_lang)
        if c.isalpha()
    ]
    lang = "".join(chars)[:2]
    return "unknown" if len(lang) < 2 else lang[:2]


def format_references(row, subfield=None):
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
        print(len(keys), len(rows))
        print(keys)
        print(row)
        return {}


def format_articles(row, subfield=None):
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


def format_key_and_value(row, subfield=None):
    try:
        _id = row["id"]
        _value = row["value"]
        collection = ''
    except (KeyError, TypeError):
        try:
            _id, _value = row
            if "^c" not in _id:
                _id += "^c"
        except ValueError as e:
            _value = "|".join(row[1:])
    _id, collection = _id.split("^c")
    if not _value:
        return {}
    _value = _value.replace("/", ";")
    items = [v for v in _value.split(";")]
    return [
        {
            "key": _id, "collection": collection,
            "value": fix_data(item), "original": item,
        }
        for item in items
    ]


def format_text_and_lang(row, subfield):
    try:
        _pid = row["pid"]
        _text = row["text"]
    except (KeyError, TypeError):
        try:
            if len(row) == 2:
                _pid, _text = row
            else:
                _pid, _text, _year = row
        except ValueError as e:
            _pid = row[0]
            _text = "|".join(row[1:])

    try:
        if "^c" in _pid:
            pid, collection = _pid.split("^c")
        else:
            pid = _pid
            collection = ""
    except:
        #print(row)
        return {}
    if not _text:
        return {}

    lang = ""
    if _text and subfield == "t" and "[title language=" in _text:
        _text = _text[_text.find("[title language="):]
        lang = _text[_text.find("=")+1:]
        lang = "".join([c for c in lang if c.isalpha()])
        lang = lang[:2]
        if "^l" not in _text:
            _text += "^l" + lang
        _text = _text[_text.find("]")+1:]

    if not _text.startswith("^"):
        _text = "^*" + _text

    if "^l" not in _text:
        _text += "^lunknown"

    subfields = {}
    for item in _text.split("^"):
        if item:
            subfields[item[0]] = item[1:]
    try:
        txt = (subfields.get(subfield, '').strip() or subfields.get("*", '').strip()).strip()
        if not txt:
            print(row)
            print(subfields)
            return {}

        return {
            "pid": pid, "collection": collection,
            "lang": format_lang(subfields["l"]), "text": fix_data(txt),
            "original": txt,
            "pub_year": pid[10:14]
        }
    except KeyError:
        return {}


def remove_diacritics(s):
    try:
        s = normalize('NFKD', s)
    except TypeError:
        s = normalize('NFKD', unicode(s, "utf-8"))
    finally:
        return s.encode('ASCII', 'ignore').decode('ASCII')


def fix_data(txt):
    txt = entity_to_char(txt)
    txt = remove_extra_spaces(txt)
    txt = remove_diacritics(txt)
    txt = txt.upper()
    while txt and not txt[0].isalnum():
        txt = txt[1:]
    while txt and not txt[-1].isalnum():
        txt = txt[:-2]
    return txt

