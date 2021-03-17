from flask import Flask, request, render_template, jsonify
import copy
from datetime import datetime
import json
from .grammdict import GrammDict

gd = GrammDict()
app = Flask(__name__)


def copy_request_args():
    """
    Copy the reauest arguments from request.args to a
    normal modifiable dictionary. Return the dictionary.
    """
    query = {}
    if request.args is None or len(request.args) <= 0:
        return query
    for field, value in request.args.items():
        query[field] = copy.deepcopy(value)
    return query


@app.route('/')
def index():
    return render_template('index.html', languages=gd.languages)


@app.route('/<lang>')
def index_lang(lang):
    if lang in gd.languages:
        return render_template('index.html', lang=lang, languages=gd.languages)
    return render_template('index.html', languages=gd.languages)


@app.route('/<lang>/add_lemma')
def add_lemma(lang):
    if lang not in gd.languages:
        return jsonify({'message': 'Такого языка нет в списке.'})
    query = copy_request_args()
    with open('query_log.txt', 'a', encoding='utf-8') as fLog:
        fLog.write(datetime.now().isoformat(timespec='seconds') + '\t' + lang + '\n')
        fLog.write(json.dumps(query, ensure_ascii=False, indent=2) + '\n\n')
    lemma, lexref, pos, tags, stems, trans_ru = gd.parse_query(lang, query)
    oldLexemes = gd.search(lang, lemma, pos)
    if len(oldLexemes) > 0:
        return jsonify({'lexemes': oldLexemes})
    gd.add_lemma(lang, lemma, lexref, pos, tags, stems, trans_ru)
    return jsonify({'message': 'OK'})


@app.route('/<lang>/add_lemma_anyway')
def add_lemma_anyway(lang):
    if lang not in gd.languages:
        return jsonify({'message': 'Такого языка нет в списке.'})
    query = copy_request_args()
    lemma, lexref, pos, tags, stems, trans_ru = gd.parse_query(lang, query)
    gd.add_lemma(lang, lemma, lexref, pos, tags, stems, trans_ru)
    return jsonify({'message': 'OK'})



if __name__ == "__main__":
    app.run(port=5500, host='0.0.0.0', debug=True)
