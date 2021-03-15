import re
import json
import os


class GrammDict:
    """
    Represents one file with the description of stems.
    """
    rxLexeme = re.compile('-lexeme\n(?: [^\r\n]+\n)+', flags=re.DOTALL)
    rxLines = re.compile('(?<=\n) ([^:\r\n]+): *([^\r\n]*)(?=\n)', flags=re.DOTALL)
    rxFieldNum = re.compile('_[0-9]+$', flags=re.DOTALL)
    with open('conf/languages.json', 'r', encoding='utf-8-sig') as fLang:
        languages = json.load(fLang)

    def __init__(self):
        self.lexemes = {}       # {lang: {(lemma, POS): text}}
        for lang in self.languages:
            self.initialize_language(lang)

    def load_dict(self, text, lang):
        """
        Find all lemmata in a string and return them as a list of lists [[key, value],...].
        """
        if lang not in self.lexemes:
            return
        curLexemes = self.rxLexeme.findall(text)
        for lex in curLexemes:
            lines = self.rxLines.findall(lex)
            lemma, pos = '', ''
            for line in lines:
                if line[0] == 'lex':
                    lemma = line[1]
                elif line[0] == 'gramm':
                    pos = ','.join(re.findall('[A-Z][A-Z_-]*', line[1]))
                if (lemma, pos) not in self.lexemes[lang]:
                    self.lexemes[lang] = [lex]
                else:
                    self.lexemes[lang].append(lex)

    def initialize_language(self, lang):
        if lang not in self.languages:
            return
        self.lexemes[lang] = {}
        repoRoot = os.path.join('web_app', lang, self.languages[lang]['repo'])
        for fname in os.listdir(repoRoot):
            if fname.endswith('.txt') and fname.startswith(self.languages[lang]['id'] + '_lexemes'):
                with open(os.path.join(repoRoot, fname), 'r', encoding='utf-8-sig') as fIn:
                    self.load_dict(fIn.read(), lang)

    def add_lemma(self, lang, lemma, pos, tags, inflType, trans_ru):
        if lang not in self.lexemes or len(lemma) <= 0 or len(pos) <= 0:
            return
        print(lemma, pos, tags, inflType, trans_ru)

    def search(self, lang, lemma, pos):
        if lang not in self.lexemes or (lemma, pos) not in self.lexemes[lang]:
            return []
        return self.lexemes[lang][(lemma, pos)]

    def parse_query(self, lang, query):
        lemma = ''
        pos = ''
        tags = ''
        inflType = ''
        trans_ru = ''
        if lang not in self.languages:
            return lemma, pos, tags, inflType, trans_ru
        for k in sorted(query):
            if k == 'lemma':
                lemma = query[k]
            elif k == 'pos':
                pos = query[k]
            elif k == 'inflType':
                inflType = query[k]
            elif k == 'trans_ru':
                trans_ru = query[k]
            else:
                if len(tags) > 0:
                    tags += ','
                tags += query[k]
        return lemma, pos, tags, inflType, trans_ru
