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
                    posTags = re.findall('[A-Z][A-Z_-]*', line[1])
                    if len(posTags) > 0:
                        pos = posTags[0]
            if (lemma, pos) not in self.lexemes[lang]:
                self.lexemes[lang][(lemma, pos)] = [lex]
            else:
                self.lexemes[lang][(lemma, pos)].append(lex)

    def initialize_language(self, lang):
        if lang not in self.languages:
            return
        self.lexemes[lang] = {}
        repoRoot = os.path.join('web_app', lang, self.languages[lang]['repo'])
        for fname in os.listdir(repoRoot):
            if fname.endswith('.txt') and fname.startswith(self.languages[lang]['id'] + '_lexemes'):
                with open(os.path.join(repoRoot, fname), 'r', encoding='utf-8-sig') as fIn:
                    self.load_dict(fIn.read(), lang)

    def add_lemma(self, lang, lemma, lexref, pos, tags, stems, trans_ru):
        if lang not in self.lexemes or len(lemma) <= 0 or len(pos) <= 0:
            return
        # print(lemma, lexref, pos, tags, stems, trans_ru)
        if len(pos) <= 0 or len(stems) <= 0:
            return
        lex = ''
        if len(lexref) > 0:
            lemma = lexref
        for stem in stems:
            lex += '-lexeme\n'
            lex += ' lex: ' + lemma + '\n'
            lex += ' gramm: ' + pos
            if len(tags) > 0:
                lex += ',' + ','.join(tags)
            lex += '\n'
            lex += ' stem: ' + stem['stem'] + '\n'
            if type(stem['paradigm']) == list:
                lex += '\n'.join(' paradigm: ' + p for p in stem['paradigm']) + '\n'
            else:
                lex += ' paradigm: ' + stem['paradigm'] + '\n'
            lex += ' trans_ru: ' + trans_ru + '\n\n'
        with open(os.path.join('web_app', lang, 'new_lexemes.txt'), 'a', encoding='utf-8') as fOut:
            fOut.write(lex)

    def search(self, lang, lemma, pos):
        if lang not in self.lexemes or (lemma, pos) not in self.lexemes[lang]:
            return []
        return self.lexemes[lang][(lemma, pos)]

    def get_stems(self, lang, lemma, pos, tags):
        stems = []
        if lang == 'udmurt':
            if pos == 'V':
                if lemma.endswith(('аны', 'яны')):
                    stems.append({
                        'stem': lemma[:-2] + '.',
                        'paradigm': 'connect_verbs-II'
                    })
                    tags.append('II')
                elif lemma.endswith('ьыны'):
                    stems.append({
                        'stem': lemma[:-4] + '.',
                        'paradigm': 'connect_verbs-I-soft'
                    })
                    tags.append('I')
                elif lemma.endswith('йыны'):
                    stems.append({
                        'stem': lemma[:-3] + '.|' + lemma[:-4] + '.',
                        'paradigm': 'connect_verbs-I'
                    })
                    tags.append('I')
                elif lemma.endswith('ыны'):
                    stems.append({
                        'stem': lemma[:-4] + '.',
                        'paradigm': 'connect_verbs-I'
                    })
                    tags.append('I')
        return stems, tags

    def fix_tags(self, lang, pos, tags):
        addTags = set()
        delTags = set()
        if 'PN' in tags and 'rus' in tags and pos != 'V':
            delTags.add('rus')
        if ('PN' not in tags and ('persn' in tags or 'famn' in tags
                                  or 'patrn' in tags or 'topn' in tags)
            and pos in ('N', 'A', 'ADJ')):
                addTags.add('PN')
        if pos != 'V':
            delTags.add('tr')
            delTags.add('intr')
            delTags.add('impers')
            delTags.add('with_abl')
            delTags.add('with_dat')
            delTags.add('with_el')
            delTags.add('with_ill')
            delTags.add('with_inf')
            delTags.add('with_instr')
        else:
            delTags.add('PN')
            delTags.add('persn')
            delTags.add('famn')
            delTags.add('patrn')
            delTags.add('topn')
            delTags.add('time_meas')
            delTags.add('body')
            delTags.add('anim')
            delTags.add('hum')
            delTags.add('transport')
            delTags.add('supernat')
        tags = list((set(tags) | addTags) - delTags)
        return tags

    def parse_query(self, lang, query):
        lemma = ''
        lexref = ''
        pos = ''
        tags = []
        stems = []
        trans_ru = ''
        if lang not in self.languages:
            return lemma, pos, tags, stems, trans_ru
        for k in sorted(query):
            print(k, query[k])
            if k == 'lemma':
                lemma = query[k]
            elif k == 'lexref':
                lexref = query[k]
            elif k == 'pos':
                pos = query[k]
            elif k == 'trans_ru':
                trans_ru = query[k]
            elif len(query[k]) > 0:
                for tag in query[k].split(','):
                    tag = tag.strip()
                    if len(tag) > 0:
                        tags.append(tag)
        stems, tags = self.get_stems(lang, lemma, pos, tags)
        tags = self.fix_tags(lang, pos, tags)
        return lemma, lexref, pos, tags, stems, trans_ru
