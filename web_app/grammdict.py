import re
import json
import os


class GrammDict:
    """
    Represents one file with the description of stems.
    """
    rxAnnotatorsLine = re.compile('^[^\t\n]*\t[^\t\n]*\t[^\t\n]*\t[^\t\n]*\t[^\t\n]*$')
    rxLexeme = re.compile('-lexeme\n(?: [^\r\n]+\n)+', flags=re.DOTALL)
    rxLines = re.compile('(?<=\n) ([^:\r\n]+): *([^\r\n]*)(?=\n)', flags=re.DOTALL)
    rxFieldNum = re.compile('_[0-9]+$', flags=re.DOTALL)
    rxLastVowel = re.compile('[аӓӑәӛеӗёиіӥоӧөӫуӱүыӹэюя]$')
    rxKomiCCSoft = re.compile('(дь|ль)$')
    rxErzyaCC = re.compile('[йслрцвнтдшчх]ь?[гкмтд]$')
    rxMokshaVoicelessPairs = re.compile('[вгджзйлр]')
    rxBuryatFrontLab = re.compile('[өү][^аоуяёюөүэе]*(?:[иыеэ]хэ)?$')
    rxBuryatFront = re.compile('[еэ][^аоуяёюөүэе]*$')
    rxBuryatBackLab = re.compile('[оу][^аоуяёюөүэе]*(?:[иыаояё]хо)?$')
    rxBuryatBack = re.compile('[ая][^аоуяёюөүэе]*$')
    rxBuryatVShortC = re.compile('[^аоуяёюөүэеыий]х[аоэ]$')
    rxBuryatVShortV = re.compile('[^аоуяёюөүэеыийьъ][аоэяёе]х[аоэ]$')
    rxBuryatVLong = re.compile('(?:[аоуяёюөүэе][аоуөүэй]|ы)х[аоэ]$')
    rxBuryatVJ = re.compile('[аоуяёюөүэеьъй][ёюяе]х[аоэ]$')
    rxBuryatVI = re.compile('их[аоэ]$')
    rxBuryatNShort = re.compile('[^аоуяёюөүыиэе][аоуяёюөүэе]$')
    rxBuryatNLong = re.compile('[аоуяёюөүэе][аоуөүэ]$')
    rxBuryatNN = re.compile('[аоуяёюөүэеыи]н$')
    rxBuryatNCC = re.compile('[^аоуяёюөүэеыийьъ][^аоуяёюөүэеыийьъ]$')
    with open('conf/languages.json', 'r', encoding='utf-8-sig') as fLang:
        languages = json.load(fLang)

    def __init__(self):
        self.lexemes = {}       # {lang: {(lemma, POS): text}}
        for lang in self.languages:
            self.initialize_language(lang)
        self.annotators = {}
        if os.path.exists('annotators.txt'):
            with open('annotators.txt', 'r', encoding='utf-8') as fAnnotators:
                for line in fAnnotators:
                    line = line.strip('\r\n')
                    if self.rxAnnotatorsLine.search(line) is None:
                        continue
                    annotator, lang, lemma, pos, stem = line.split('\t')
                    if annotator not in self.annotators:
                        self.annotators[annotator] = set()
                    self.annotators[annotator].add((lang, lemma, pos, stem))

    def add_lex_to_dict(self, lang, lemma, pos, text):
        if (lemma, pos) not in self.lexemes[lang]:
            self.lexemes[lang][(lemma, pos)] = [text]
        else:
            self.lexemes[lang][(lemma, pos)].append(text)

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
            self.add_lex_to_dict(lang, lemma, pos, lex)

    def initialize_language(self, lang):
        if lang not in self.languages:
            return
        self.lexemes[lang] = {}
        # Analyzer dictionary
        repoRoot = os.path.join('web_app', lang, self.languages[lang]['repo'])
        for fname in os.listdir(repoRoot):
            if fname.endswith('.txt') and fname.startswith(self.languages[lang]['id'] + '_lexemes'):
                with open(os.path.join(repoRoot, fname), 'r', encoding='utf-8-sig') as fIn:
                    self.load_dict(fIn.read(), lang)
        # Words entered previously
        langRoot = os.path.join('web_app', lang)
        for fname in os.listdir(langRoot):
            if fname.endswith('.txt') and fname.startswith('new_lexemes'):
                with open(os.path.join(langRoot, fname), 'r', encoding='utf-8-sig') as fIn:
                    self.load_dict(fIn.read(), lang)

    def add_lemma(self, lang, annotator, lemma, lexref, pos, tags, stems, trans_ru):
        if lang not in self.lexemes or len(lemma) <= 0 or len(pos) <= 0:
            return
        # print(lemma, lexref, pos, tags, stems, trans_ru)
        if len(pos) <= 0 or len(lemma) <= 0 or len(stems) <= 0:
            return
        if 'PN' in tags:
            lemma = lemma[0].upper() + lemma[1:]
            if len(trans_ru) > 0:
                trans_ru = trans_ru[0].upper() + trans_ru[1:]
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
            lex += ' stem: ' + stem['stem'].lower() + '\n'
            if type(stem['paradigm']) == list:
                lex += '\n'.join(' paradigm: ' + p for p in stem['paradigm']) + '\n'
            else:
                lex += ' paradigm: ' + stem['paradigm'] + '\n'
            lex += ' trans_ru: ' + trans_ru + '\n\n'
        fname = 'new_lexemes_' + pos + '.txt'
        if 'PN' in tags:
            fname = 'new_lexemes_PN.txt'
        elif 'prod_deriv' in tags:
            fname = 'new_lexrules.txt'
        with open(os.path.join('web_app', lang, fname),
                  'a', encoding='utf-8') as fOut:
            fOut.write(lex)
        self.add_lex_to_dict(lang, lemma, pos, lex)

        if len(annotator) > 0:
            joinedStem = '$'.join(stem['stem'] for stem in sorted(stems))
            if annotator not in self.annotators:
                self.annotators[annotator] = set()
            self.annotators[annotator].add((lang, lemma, pos, joinedStem))
            with open('annotators.txt', 'a', encoding='utf-8') as fAnnotators:
                fAnnotators.write(annotator + '\t'
                                  + lang + '\t'
                                  + lemma + '\t'
                                  + pos + '\t'
                                  + joinedStem + '\n')

    def search(self, lang, lemma, pos):
        if lang not in self.lexemes or (lemma, pos) not in self.lexemes[lang]:
            return []
        return self.lexemes[lang][(lemma, pos)]

    def annotator_stats(self, annotator):
        if annotator not in self.annotators:
            return 0
        return len(self.annotators[annotator])

    def get_stems_udmurt(self, lemma, pos, tags):
        stems = []
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
                    'stem': lemma[:-3] + '.',
                    'paradigm': 'connect_verbs-I'
                })
                tags.append('I')
        elif pos in ('ADJ', 'ADJPRO'):
            if lemma.endswith('ь'):
                stems.append({
                    'stem': lemma[:-1] + '.',
                    'paradigm': 'connect_adjectives-soft'
                })
            elif lemma.endswith('й'):
                stems.append({
                    'stem': lemma[:-1] + '.',
                    'paradigm': 'connect_adjectives-j'
                })
            else:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'connect_adjectives'
                })
                if 'poss_y' in tags:
                    stems.append({
                        'stem': lemma + '.',
                        'paradigm': 'Noun-num-consonant-y'
                    })
        elif pos == 'N':
            if lemma.endswith('ь'):
                stems.append({
                    'stem': lemma[:-1] + '.',
                    'paradigm': 'Noun-num-soft'
                })
                if 'poss_y' in tags:
                    stems.append({
                        'stem': lemma[:-1] + '.',
                        'paradigm': 'Noun-num-soft-y'
                    })
            elif lemma.endswith('й'):
                stems.append({
                    'stem': lemma[:-1] + '.',
                    'paradigm': 'Noun-num-j'
                })
                if 'poss_y' in tags:
                    stems.append({
                        'stem': lemma[:-1] + '.',
                        'paradigm': 'Noun-num-j-y'
                    })
            elif self.rxLastVowel.search(lemma) is not None:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'Noun-num-vowel'
                })
                if 'poss_y' in tags:
                    stems.append({
                        'stem': lemma + '.',
                        'paradigm': 'Noun-num-vowel-y'
                    })
            else:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'Noun-num-consonant'
                })
                if 'poss_y' in tags:
                    stems.append({
                        'stem': lemma + '.',
                        'paradigm': 'Noun-num-consonant-y'
                    })
        elif pos in ('ADV', 'ADVPRO'):
            stems.append({
                'stem': lemma + '.',
                'paradigm': 'connect_adverbs'
            })
        else:
            stems.append({
                'stem': lemma + '.',
                'paradigm': 'Comparative'
            })
        return stems, tags

    def get_stems_komi_zyrian(self, lemma, pos, tags):
        stems = []
        if pos == 'V':
            if lemma.endswith('явны'):
                stems.append({
                    'stem': lemma[:-4] + '.',
                    'paradigm': 'V-yavny'
                })
            elif lemma.endswith('авны'):
                stems.append({
                    'stem': lemma[:-4] + '.',
                    'paradigm': 'V-avny'
                })
            elif lemma.endswith('вны'):
                stems.append({
                    'stem': lemma[:-3] + '.',
                    'paradigm': 'V-vny'
                })
            elif lemma.endswith('ьыны'):
                stems.append({
                    'stem': lemma[:-4] + '.',
                    'paradigm': 'V-yny-soft'
                })
            elif lemma.endswith('ыны'):
                stems.append({
                    'stem': lemma[:-3] + '.',
                    'paradigm': 'V-yny'
                })
            elif lemma.endswith('ьны'):
                stems.append({
                    'stem': lemma[:-3] + '.',
                    'paradigm': 'V-ny-soft'
                })
            elif lemma.endswith('ны'):
                stems.append({
                    'stem': lemma[:-2] + '.',
                    'paradigm': 'V-ny'
                })
        elif pos in ('A', 'APRO'):
            if lemma.endswith('ь'):
                stems.append({
                    'stem': '.' + lemma[:-1] + '.',
                    'paradigm': 'Adj-soft'
                })
            elif lemma.endswith('й'):
                stems.append({
                    'stem': '.' + lemma[:-1] + '.',
                    'paradigm': 'Adj-j'
                })
            elif self.rxLastVowel.search(lemma) is not None:
                stems.append({
                    'stem': '.' + lemma + '.',
                    'paradigm': 'Adj-vowel'
                })
            else:
                stems.append({
                    'stem': '.' + lemma + '.',
                    'paradigm': 'Adj-consonant'
                })
        elif pos == 'N':
            if 'infl_obl_j' in tags:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'Noun-num-obl_j'
                })
            elif 'infl_obl_k' in tags:
                stems.append({
                    'stem': lemma + '.|' + lemma + 'к.',
                    'paradigm': 'Noun-num-obl_cons'
                })
            elif 'infl_v_l' in tags and lemma.endswith('в'):
                stems.append({
                    'stem': lemma + '.|' + lemma[:-1] + 'л.',
                    'paradigm': 'Noun-num-v_l'
                })
            elif self.rxKomiCCSoft.search(lemma) is not None:
                stems.append({
                    'stem': lemma + '.|' + lemma[:-1] + lemma[-2] + '.',
                    'paradigm': 'Noun-num-CC\''
                })
            elif lemma.endswith('дз'):
                stems.append({
                    'stem': lemma + '.|' + lemma[:-1] + lemma[-2] + '.',
                    'paradigm': 'Noun-num-ddz'
                })
            elif 'infl_pi' in tags and lemma.endswith('пи'):
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'Noun-num-pi'
                })
            elif lemma.endswith('ь'):
                stems.append({
                    'stem': lemma[:-1] + '.',
                    'paradigm': 'Noun-num-soft'
                })
            elif lemma.endswith('й'):
                stems.append({
                    'stem': lemma[:-1] + '.',
                    'paradigm': 'Noun-num-j'
                })
            elif self.rxLastVowel.search(lemma) is not None:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'Noun-num-vowel'
                })
            else:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'Noun-num-consonant'
                })
        elif pos in ('ADV', 'ADVPRO'):
            stems.append({
                'stem': lemma + '.',
                'paradigm': 'Adverbials-final'
            })
        else:
            stems.append({
                'stem': lemma + '.',
                'paradigm': 'Clitics'
            })
        return stems, tags

    def get_stems_meadow_mari(self, lemma, pos, tags):
        stems = []
        if pos == 'V':
            if lemma.endswith('аш'):
                if 'conj_a' in tags:
                    stems.append({
                        'stem': lemma[:-2] + '.',
                        'paradigm': 'V_a'
                    })
                else:
                    stems.append({
                        'stem': lemma[:-2] + '.',
                        'paradigm': 'V_e'
                    })
            elif lemma.endswith('яш'):
                if 'conj_a' in tags:
                    stems.append({
                        'stem': lemma[:-2] + '.|' + lemma[:-2] + 'й.',
                        'paradigm': 'V_ya'
                    })
                else:
                    stems.append({
                        'stem': lemma[:-2] + '.|' + lemma[:-2] + 'й.',
                        'paradigm': 'V_ye'
                    })
            else:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'Clitics'
                })
        elif pos in ('A', 'APRO'):
            if lemma.endswith('ь'):
                stems.append({
                    'stem': lemma + '.|' + lemma[:-1] + '.',
                    'paradigm': 'A_soft'
                })
            elif lemma.endswith('й'):
                stems.append({
                    'stem': lemma + '.|' + lemma[:-1] + '.',
                    'paradigm': 'A_j'
                })
            elif self.rxLastVowel.search(lemma) is None or 'consonant' in tags:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'A_consonant'
                })
            elif 'oxyton' in tags:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'A_oxyton'
                })
            else:
                stems.append({
                    'stem': lemma + '.|' + lemma[:-1] + 'ы.|' + lemma[:-1] + '.',
                    'paradigm': 'A_paroxyton_v_weak'
                })
        elif pos == 'N':
            if lemma.endswith('ь'):
                stems.append({
                    'stem': lemma + '.|' + lemma[:-1] + '.',
                    'paradigm': 'N_soft'
                })
            elif lemma.endswith('й'):
                stems.append({
                    'stem': lemma + '.|' + lemma[:-1] + '.',
                    'paradigm': 'N_j'
                })
            elif self.rxLastVowel.search(lemma) is None or 'consonant' in tags:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'N_consonant'
                })
            elif 'oxyton' in tags:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'N_oxyton'
                })
            else:
                stems.append({
                    'stem': lemma + '.|' + lemma[:-1] + 'ы.|' + lemma[:-1] + '.',
                    'paradigm': 'N_paroxyton_v_weak'
                })
        elif pos in ('ADV', 'POST'):
            stems.append({
                'stem': lemma + '.',
                'paradigm': 'POST_ADV_Poss'
            })
        else:
            stems.append({
                'stem': lemma + '.',
                'paradigm': 'Clitics'
            })
        return stems, tags

    def get_stems_erzya(self, lemma, pos, tags):
        stems = []
        if pos == 'V':
            if lemma.endswith('домс'):
                stems.append({
                    'stem': lemma[:-4] + '.',
                    'paradigm': 'V-do'
                })
            elif lemma.endswith('омс'):
                stems.append({
                    'stem': lemma[:-3] + '.',
                    'paradigm': 'V-o'
                })
            elif lemma.endswith('ёмс'):
                stems.append({
                    'stem': lemma[:-3] + '.',
                    'paradigm': 'V-yo'
                })
            elif lemma.endswith('емс'):
                stems.append({
                    'stem': lemma[:-3] + '.',
                    'paradigm': 'V-ye'
                })
            elif lemma.endswith('эмс'):
                stems.append({
                    'stem': lemma[:-3] + '.',
                    'paradigm': 'V-e'
                })
            elif lemma.endswith('амс'):
                stems.append({
                    'stem': lemma[:-3] + '.',
                    'paradigm': 'V-a'
                })
            elif lemma.endswith('ямс'):
                stems.append({
                    'stem': lemma[:-3] + '.',
                    'paradigm': 'V-ya'
                })
            else:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'Clitics'
                })
        elif pos in ('A', 'APRO'):
            if lemma.endswith('ь'):
                stems.append({
                    'stem': lemma[:-1] + '.',
                    'paradigm': 'A-front-soft'
                })
            elif lemma.endswith('й'):
                stems.append({
                    'stem': lemma[:-1] + '.',
                    'paradigm': 'A-front-j'
                })
            elif lemma.endswith('о'):
                if self.rxErzyaCC.search(lemma[:-1]) is not None:
                    stems.append({
                        'stem': lemma + '.|' + lemma[:-1] + '.',
                        'paradigm': 'A-back'
                    })
                else:
                    stems.append({
                        'stem': lemma + '.',
                        'paradigm': 'A-back'
                    })
            elif lemma.endswith('е'):
                if self.rxErzyaCC.search(lemma[:-1]) is not None:
                    stems.append({
                        'stem': lemma + '.|' + lemma[:-1] + '.',
                        'paradigm': 'A-front'
                    })
                else:
                    stems.append({
                        'stem': lemma + '.',
                        'paradigm': 'A-front'
                    })
            else:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'A-front'
                })
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'A-back'
                })
        elif pos == 'N':
            if lemma.endswith('ь'):
                stems.append({
                    'stem': lemma[:-1] + '.',
                    'paradigm': 'N-front-soft'
                })
            elif lemma.endswith('й'):
                stems.append({
                    'stem': lemma[:-1] + '.',
                    'paradigm': 'N-front-j'
                })
            elif lemma.endswith('о'):
                if self.rxErzyaCC.search(lemma[:-1]) is not None:
                    stems.append({
                        'stem': lemma + '.|' + lemma[:-1] + '.',
                        'paradigm': 'N-back'
                    })
                else:
                    stems.append({
                        'stem': lemma + '.',
                        'paradigm': 'N-back'
                    })
            elif lemma.endswith('е'):
                if self.rxErzyaCC.search(lemma[:-1]) is not None:
                    stems.append({
                        'stem': lemma + '.|' + lemma[:-1] + '.',
                        'paradigm': 'N-front'
                    })
                else:
                    stems.append({
                        'stem': lemma + '.',
                        'paradigm': 'N-front'
                    })
            else:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'N-front'
                })
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'N-back'
                })
        else:
            stems.append({
                'stem': lemma + '.',
                'paradigm': 'Clitics'
            })
        return stems, tags

    def get_stems_moksha(self, lemma, pos, tags):
        stems = []
        if pos == 'V':
            if lemma.endswith('домс'):
                stems.append({
                    'stem': lemma[:-4] + '.',
                    'paradigm': 'V-do'
                })
            elif lemma.endswith('омс'):
                stems.append({
                    'stem': lemma[:-3] + '.',
                    'paradigm': 'V-o'
                })
            elif lemma.endswith('ёмс'):
                stems.append({
                    'stem': lemma[:-3] + '.',
                    'paradigm': 'V-yo'
                })
            elif lemma.endswith('емс'):
                stems.append({
                    'stem': lemma[:-3] + '.',
                    'paradigm': 'V-ye'
                })
            elif lemma.endswith('эмс'):
                stems.append({
                    'stem': lemma[:-3] + '.',
                    'paradigm': 'V-e'
                })
            elif lemma.endswith('амс'):
                stems.append({
                    'stem': lemma[:-3] + '.',
                    'paradigm': 'V-a'
                })
            elif lemma.endswith('ямс'):
                stems.append({
                    'stem': lemma[:-3] + '.',
                    'paradigm': 'V-ya'
                })
            else:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'Clitics'
                })
        elif pos in ('A', 'APRO'):
            if lemma.endswith(('рь', 'ль')):
                stems.append({
                    'stem': lemma[:-1] + '.|' + lemma + './/' + lemma + 'х.',
                    'paradigm': 'A-front-soft-x'
                })
            elif lemma.endswith('ь'):
                stems.append({
                    'stem': lemma[:-1] + '.',
                    'paradigm': 'A-front-soft'
                })
            elif lemma.endswith('й'):
                stems.append({
                    'stem': lemma[:-1] + '.|' + lemma + 'х.',
                    'paradigm': 'A-front-j'
                })
            elif self.rxLastVowel.search(lemma) is not None:
                if self.rxMokshaVoicelessPairs.search(lemma[-1]) is not None:
                    if lemma[-1] in 'рл':
                        stems.append({
                            'stem': lemma + '.|' + lemma + './/' + lemma + 'х.',
                            'paradigm': 'A-consonant'
                        })
                    elif lemma[-1] == 'в':
                        stems.append({
                            'stem': lemma + '.|' + lemma + './/' + lemma[:-1] + 'ф.',
                            'paradigm': 'A-consonant'
                        })
                    elif lemma[-1] == 'г':
                        stems.append({
                            'stem': lemma + '.|' + lemma + './/' + lemma[:-1] + 'к.',
                            'paradigm': 'A-consonant'
                        })
                    elif lemma[-1] == 'д':
                        stems.append({
                            'stem': lemma + '.|' + lemma + './/' + lemma[:-1] + 'т.',
                            'paradigm': 'A-consonant'
                        })
                    elif lemma[-1] == 'ж':
                        stems.append({
                            'stem': lemma + '.|' + lemma + './/' + lemma[:-1] + 'ш.',
                            'paradigm': 'A-consonant'
                        })
                    elif lemma[-1] == 'з':
                        stems.append({
                            'stem': lemma + '.|' + lemma + './/' + lemma[:-1] + 'с.',
                            'paradigm': 'A-consonant'
                        })
            elif lemma.endswith(('у', 'ю')):
                stems.append({
                    'stem': lemma + './/' + lemma + 'во.|' + lemma + './/' + lemma + 'ф.',
                    'paradigm': 'A-vowel'
                })
            elif lemma.endswith('и'):
                stems.append({
                    'stem': lemma + '.|' + lemma + './/' + lemma + 'х.',
                    'paradigm': 'A-iy'
                })
            elif self.rxErzyaCC.search(lemma[:-1]) is not None:
                if lemma[-2] in 'йрл':
                    stems.append({
                        'stem': lemma + '.|' + lemma + './/' + lemma[:-1] + 'х.',
                        'paradigm': 'A-vowel'
                    })
                elif lemma[-2] == 'в':
                    stems.append({
                        'stem': lemma + '.|' + lemma + './/' + lemma[:-2] + 'ф.',
                        'paradigm': 'A-vowel'
                    })
                elif lemma[-2] == 'г':
                    stems.append({
                        'stem': lemma + '.|' + lemma + './/' + lemma[:-2] + 'к.',
                        'paradigm': 'A-vowel'
                    })
                elif lemma[-2] == 'д':
                    stems.append({
                        'stem': lemma + '.|' + lemma + './/' + lemma[:-2] + 'т.',
                        'paradigm': 'A-vowel'
                    })
                elif lemma[-2] == 'ж':
                    stems.append({
                        'stem': lemma + '.|' + lemma + './/' + lemma[:-2] + 'ш.',
                        'paradigm': 'A-vowel'
                    })
                elif lemma[-2] == 'з':
                    stems.append({
                        'stem': lemma + '.|' + lemma + './/' + lemma[:-2] + 'с.',
                        'paradigm': 'A-vowel'
                    })
                else:
                    stems.append({
                        'stem': lemma + '.|' + lemma + './/' + lemma[:-1] + '.',
                        'paradigm': 'A-vowel'
                    })
            else:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'A-vowel'
                })
        elif pos == 'N':
            if lemma.endswith(('рь', 'ль')):
                stems.append({
                    'stem': lemma[:-1] + '.|' + lemma + './/' + lemma + 'х.',
                    'paradigm': 'N-front-soft-x'
                })
            elif lemma.endswith('ь'):
                stems.append({
                    'stem': lemma[:-1] + '.',
                    'paradigm': 'N-front-soft'
                })
            elif lemma.endswith('й'):
                stems.append({
                    'stem': lemma[:-1] + '.|' + lemma + 'х.',
                    'paradigm': 'N-front-j'
                })
            elif self.rxLastVowel.search(lemma) is not None:
                if self.rxMokshaVoicelessPairs.search(lemma[-1]) is not None:
                    if lemma[-1] in 'рл':
                        stems.append({
                            'stem': lemma + '.|' + lemma + './/' + lemma + 'х.',
                            'paradigm': 'N-consonant'
                        })
                    elif lemma[-1] == 'в':
                        stems.append({
                            'stem': lemma + '.|' + lemma + './/' + lemma[:-1] + 'ф.',
                            'paradigm': 'N-consonant'
                        })
                    elif lemma[-1] == 'г':
                        stems.append({
                            'stem': lemma + '.|' + lemma + './/' + lemma[:-1] + 'к.',
                            'paradigm': 'N-consonant'
                        })
                    elif lemma[-1] == 'д':
                        stems.append({
                            'stem': lemma + '.|' + lemma + './/' + lemma[:-1] + 'т.',
                            'paradigm': 'N-consonant'
                        })
                    elif lemma[-1] == 'ж':
                        stems.append({
                            'stem': lemma + '.|' + lemma + './/' + lemma[:-1] + 'ш.',
                            'paradigm': 'N-consonant'
                        })
                    elif lemma[-1] == 'з':
                        stems.append({
                            'stem': lemma + '.|' + lemma + './/' + lemma[:-1] + 'с.',
                            'paradigm': 'N-consonant'
                        })
            elif lemma.endswith(('у', 'ю')):
                stems.append({
                    'stem': lemma + './/' + lemma + 'во.|' + lemma + './/' + lemma + 'ф.',
                    'paradigm': 'N-vowel'
                })
            elif lemma.endswith('и'):
                stems.append({
                    'stem': lemma + '.|' + lemma + './/' + lemma + 'х.',
                    'paradigm': 'N-iy'
                })
            elif self.rxErzyaCC.search(lemma[:-1]) is not None:
                if lemma[-2] in 'йрл':
                    stems.append({
                        'stem': lemma + '.|' + lemma + './/' + lemma[:-1] + 'х.',
                        'paradigm': 'N-vowel'
                    })
                elif lemma[-2] == 'в':
                    stems.append({
                        'stem': lemma + '.|' + lemma + './/' + lemma[:-2] + 'ф.',
                        'paradigm': 'N-vowel'
                    })
                elif lemma[-2] == 'г':
                    stems.append({
                        'stem': lemma + '.|' + lemma + './/' + lemma[:-2] + 'к.',
                        'paradigm': 'N-vowel'
                    })
                elif lemma[-2] == 'д':
                    stems.append({
                        'stem': lemma + '.|' + lemma + './/' + lemma[:-2] + 'т.',
                        'paradigm': 'N-vowel'
                    })
                elif lemma[-2] == 'ж':
                    stems.append({
                        'stem': lemma + '.|' + lemma + './/' + lemma[:-2] + 'ш.',
                        'paradigm': 'N-vowel'
                    })
                elif lemma[-2] == 'з':
                    stems.append({
                        'stem': lemma + '.|' + lemma + './/' + lemma[:-2] + 'с.',
                        'paradigm': 'N-vowel'
                    })
                else:
                    stems.append({
                        'stem': lemma + '.|' + lemma + './/' + lemma[:-1] + '.',
                        'paradigm': 'N-vowel'
                    })
            else:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'N-vowel'
                })
        else:
            stems.append({
                'stem': lemma + '.',
                'paradigm': 'Clitics'
            })
        return stems, tags

    def get_stems_buryat(self, lemma, pos, tags):
        stems = []
        harmony = 'back'
        if 'syn_back' in tags:
            harmony = 'back'
        elif 'syn_back_lab' in tags:
            harmony = 'back-lab'
        elif 'syn_front' in tags:
            harmony = 'front'
        elif 'syn_front_lab' in tags:
            harmony = 'front-lab'
        else:
            # Determine the harmony based on vowels
            if self.rxBuryatFrontLab.search(lemma) is not None:
                harmony = 'front-lab'
            elif self.rxBuryatFront.search(lemma) is not None:
                harmony = 'front'
            elif self.rxBuryatBackLab.search(lemma) is not None:
                harmony = 'back-lab'
            elif self.rxBuryatBack.search(lemma) is not None:
                harmony = 'back'
        if pos == 'V':
            if self.rxBuryatVShortV.search(lemma) is not None:
                stems.append({
                    'stem': lemma[:-2] + '.|' + lemma[:-3] + '.',
                    'paradigm': 'short-' + harmony
                })
            elif self.rxBuryatVShortC.search(lemma) is not None:
                addV = 'а'
                if harmony.startswith('front'):
                    addV = 'э'
                elif harmony == 'back-lab':
                    addV = 'о'
                stems.append({
                    'stem': lemma[:-2] + './/' + lemma[:-2] + addV + '.|' + lemma[:-2] + '.',
                    'paradigm': 'short-' + harmony
                })
            elif self.rxBuryatVLong.search(lemma) is not None:
                stems.append({
                    'stem': lemma[:-2] + '.',
                    'paradigm': 'long-' + harmony
                })
            elif self.rxBuryatVI.search(lemma) is not None:
                stems.append({
                    'stem': lemma[:-2] + '.|' + lemma[:-3] + '.',
                    'paradigm': 'i-palat-' + harmony
                })
            elif self.rxBuryatVJ.search(lemma) is not None:
                stems.append({
                    'stem': lemma[:-2] + '.|' + lemma[:-3] + '.',
                    'paradigm': 'j-' + harmony
                })
        elif pos == 'N':
            if harmony == 'front-lab':
                harmony = 'front'
            if self.rxBuryatNN.search(lemma) is not None:
                if 'decl_unstable_n' in tags:
                    paradigm = 'unstable_n'
                    stems.append({
                        'stem': lemma + '.|' + lemma[:-1] + '.|' + lemma[:-2] + '.',
                        'paradigm': 'N-' + harmony + '-unstable_n-case'
                    })
                elif 'decl_ng' in tags:
                    paradigm = 'ng'
                    stems.append({
                        'stem': lemma + '.',
                        'paradigm': 'N-' + harmony + '-ng-case'
                    })
                else:
                    stems.append({
                        'stem': lemma + '.',
                        'paradigm': 'N-' + harmony + '-velar-cons-case'
                    })
            elif lemma.endswith('ь'):
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'N-' + harmony + '-palat-cons-case'
                })
            elif lemma.endswith('ой'):
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'N-back-oj-case'
                })
            elif lemma.endswith('й'):
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'N-' + harmony + '-y-case'
                })
            elif lemma.endswith('ии'):
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'N-' + harmony + '-i-long-case'
                })
            elif lemma.endswith('и'):
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'N-' + harmony + '-i-short-case'
                })
            elif self.rxBuryatNCC.search(lemma) is not None:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'N-' + harmony + '-CC-case'
                })
            elif self.rxBuryatNLong.search(lemma) is not None:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'N-' + harmony + '-long-case'
                })
            elif self.rxBuryatNShort.search(lemma) is not None:
                stems.append({
                    'stem': lemma + '.|' + lemma[:-1] + '.',
                    'paradigm': 'N-' + harmony + '-case'
                })
        elif pos == 'A':
            stems.append({
                'stem': lemma + '.',
                'paradigm': 'predic_non_verbal'
            })
        else:
            stems.append({
                'stem': lemma + '.',
                'paradigm': 'unchangeable'
            })
        return stems, tags

    def get_stems_ossetic(self, lemma, pos, tags):
        stems = []
        if pos == 'V':
            stem1 = stem2 = stem3 = lemma[:-2]
            if 'conj_i_y' in tags:
                stem2 = re.sub('[иу]([^аеёиоуэюяӕ]*)$', 'ы\\1', stem2)
                stem3 = re.sub('[иу]([^аеёиоуэюяӕ]*)$', 'ы\\1', stem3)
            elif 'conj_ae_a' in tags:
                stem2 = re.sub('ӕ([^аеёиоуэюяӕ]*)$', 'а\\1', stem2)
                stem3 = re.sub('ӕ([^аеёиоуэюяӕ]*)$', 'а\\1', stem3)
            elif 'conj_a_ae' in tags:
                stem2 = re.sub('а([^аеёиоуэюяӕ]*)$', 'ӕ\\1', stem2)
                stem3 = re.sub('а([^аеёиоуэюяӕ]*)$', 'ӕ\\1', stem3)
            elif 'conj_au_0' in tags:
                stem2 = re.sub('[аӕ]у([^аеёиоуэюяӕ]*)$', '\\1', stem2)
                stem3 = re.sub('[аӕ]у([^аеёиоуэюяӕ]*)$', '\\1', stem3)
            if 'conj_d_s' in tags:
                stem2 = re.sub('(д|сс)$', 'c', stem2)
                stem3 = re.sub('(д|сс)$', 'c', stem3)
            elif 'conj_dz_gh' in tags:
                stem2 = re.sub('дз$', 'гъ', stem2)
                stem3 = re.sub('дз$', 'гъ', stem3)
            elif 'conj_j_d' in tags:
                stem2 = re.sub('й$', 'д', stem2)
                stem3 = re.sub('й$', 'д', stem3)
            elif 'conj_yn_d' in tags:
                stem2 = re.sub('ын$', 'д', stem2)
                stem3 = re.sub('ын$', 'д', stem3)
            if 'conj_t_t' in tags:
                stem2 += 'т'
                stem3 += 'т'
            elif 'conj_yd_yd' in tags:
                stem2 += 'ыд'
                stem3 += 'ыд'
            elif 'conj_d_d' in tags:
                stem2 += 'д'
                stem3 += 'д'
            elif 'conj_yd_d' in tags:
                stem2 += 'ыд'
                stem3 += 'д'
            elif 'conj_yd_t' in tags:
                stem2 += 'ыд'
                stem3 += 'т'
            elif 'conj_dt_d' in tags:
                stem2 += 'дт'
                stem3 += 'д'
            elif 'conj_ydt_yd' in tags:
                stem2 += 'ыдт'
                stem3 += 'ыд'
            elif 'conj_t_d' in tags:
                stem2 += 'т'
                stem3 += 'д'
            elif 'conj_st_st' in tags:
                stem2 += 'ст'
                stem3 += 'ст'
            if stem1 == stem2 == stem3:
                stem = stem1 + '.'
            else:
                stem = stem1 + '.|' + stem2 + '.|' + stem3 + '.'
            stem = re.sub('\\bӕ(\\w+)\\.', 'ӕ\\1.//\\1.', stem)
            if 'tr' in tags:
                stems.append({
                    'stem': stem,
                    'paradigm': 'Vtr'
                })
            else:
                stems.append({
                    'stem': stem,
                    'paradigm': 'Vintr'
                })
        elif pos in ('N', 'ADJ'):
            stem1 = stem2 = stem3 = lemma
            if 'decl_a_ae' in tags:
                stem3 = re.sub('[ао]([^аеёиоэюяӕ]*)$', 'ӕ\\1', stem3)
            elif 'decl_ae_0' in tags:
                stem3 = re.sub('[ӕы]([^аеёиоыэюяӕ]*)$', '\\1', stem3)
            if 'decl_g_dzh' in tags:
                stem2 = re.sub('кк$', 'чч', stem2)
                stem2 = re.sub('къ$', 'чъ', stem2)
                stem2 = re.sub('к$', 'ч', stem2)
                stem2 = re.sub('г$', 'дж', stem2)
                if 'decl_pl_y' in tags:
                    stem3 = re.sub('кк$', 'чч', stem3)
                    stem3 = re.sub('къ$', 'чъ', stem3)
                    stem3 = re.sub('к$', 'ч', stem3)
                    stem3 = re.sub('г$', 'дж', stem3)
            if 'decl_pl_y' in tags:
                stem3 += 'ы'
                stem3 = re.sub('([сту])\\1джы$', '\\1джы', stem3)
            elif 'decl_pl_ty' in tags:
                stem3 += 'ты'
            elif 'decl_pl_uy' in tags:
                stem3 += 'уы'
            elif 'decl_pl_n' in tags:
                stem3 = re.sub('н$', '', stem3)
            if stem1 == stem2 == stem3:
                stem = stem1 + '.'
            else:
                stem = stem1 + '.|' + stem2 + '.|' + stem3 + '.'
            stem = re.sub('\\bӕ(\\w+)\\.', 'ӕ\\1.//\\1.', stem)
            if 'Nct' in tags:
                stems.append({
                    'stem': stem,
                    'paradigm': 'Nct'
                })
            elif 'Nctt' in tags:
                stems.append({
                    'stem': stem,
                    'paradigm': 'Nctt'
                })
            else:
                stems.append({
                    'stem': stem,
                    'paradigm': 'Nv'
                })
        else:
            stems.append({
                'stem': lemma + '.',
                'paradigm': 'ZERO'
            })
        return stems, tags

    def get_stems(self, lang, lemma, pos, tags):
        stems = []
        if lang == 'udmurt':
            stems, tags = self.get_stems_udmurt(lemma, pos, tags)
        elif lang == 'komi_zyrian':
            stems, tags = self.get_stems_komi_zyrian(lemma, pos, tags)
        elif lang == 'meadow_mari':
            stems, tags = self.get_stems_meadow_mari(lemma, pos, tags)
        elif lang == 'erzya':
            stems, tags = self.get_stems_erzya(lemma, pos, tags)
        elif lang == 'moksha':
            stems, tags = self.get_stems_moksha(lemma, pos, tags)
        elif lang == 'buryat':
            stems, tags = self.get_stems_buryat(lemma, pos, tags)
        elif lang == 'ossetic':
            stems, tags = self.get_stems_ossetic(lemma, pos, tags)
        return stems, tags

    def fix_tags(self, lang, pos, tags):
        addTags = set()
        delTags = {'poss_yz',
                   'consonant', 'oxyton', 'paroxyton', 'conj_a', 'conj_e',
                   'infl_obl_j', 'infl_obl_k', 'infl_pi', 'infl_v_l',
                   'decl_unstable_n', 'decl_ng', 'decl_n',
                   'syn_front', 'syn_front_lab', 'syn_back', 'syn_back_lab',
                   'Nv', 'Nct', 'Nctt',
                   'decl_pl_y', 'decl_pl_ty', 'decl_pl_uy', 'decl_pl_n',
                   'decl_a_ae', 'decl_ae_0', 'decl_g_dzh',
                   'conj_t_t', 'conj_yd_yd', 'conj_d_d', 'conj_yd_d',
                   'conj_yd_t', 'conj_dt_d', 'conj_ydt_yd', 'conj_t_d', 'conj_st_st',
                   'conj_i_y', 'conj_ae_a', 'conj_a_ae', 'conj_au_0',
                   'conj_d_s', 'conj_dz_gh', 'conj_j_d', 'conj_yn_d'
                   }
        if 'PN' in tags and 'rus' in tags and pos != 'V':
            delTags.add('rus')
        if ('PN' not in tags and ('persn' in tags or 'famn' in tags
                                  or 'patrn' in tags or 'topn' in tags)
            and pos in ('N', 'A', 'ADJ')):
                addTags.add('PN')
        if lang == 'ossetic' and pos == 'N':
            if 'anim' not in tags and 'inanim' not in tags:
                addTags.add('inanim')
            if 'human' not in tags and 'nonhuman' not in tags:
                addTags.add('nonhuman')
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
            delTags.add('inanim')
            delTags.add('hum')
            delTags.add('human')
            delTags.add('nonhuman')
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
        annotator = ''
        if lang not in self.languages:
            return annotator, lemma, pos, tags, stems, trans_ru
        for k in sorted(query):
            if k == 'lemma':
                lemma = query[k].strip()
            elif k == 'lexref':
                lexref = query[k].strip()
            elif k == 'pos':
                pos = query[k].strip()
            elif k == 'trans_ru':
                trans_ru = query[k].strip()
            elif k == 'annotator':
                annotator = query[k].strip()
            elif len(query[k]) > 0:
                for tag in query[k].split(','):
                    tag = tag.strip()
                    if len(tag) > 0:
                        tags.append(tag)
        stems, tags = self.get_stems(lang, lemma, pos, tags)
        tags = self.fix_tags(lang, pos, tags)
        return annotator, lemma, lexref, pos, tags, stems, trans_ru
