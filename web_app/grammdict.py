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
    rxLastVowel = re.compile('[аӓӑәӛеӗёиіӥоӧөӫуӱүыӹэюя]$')
    rxKomiCCSoft = re.compile('(дь|ль)$')
    rxErzyaCC = re.compile('[йслрцвнтдшчх]ь?[гкмтд]$')
    rxMokshaVoicelessPairs = re.compile('[вгджзйлр]')
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
        with open(os.path.join('web_app', lang, 'new_lexemes_' + pos + '.txt'), 'a', encoding='utf-8') as fOut:
            fOut.write(lex)

    def search(self, lang, lemma, pos):
        if lang not in self.lexemes or (lemma, pos) not in self.lexemes[lang]:
            return []
        return self.lexemes[lang][(lemma, pos)]

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
                    'stem': lemma[:-1] + '.',
                    'paradigm': 'Adj-soft'
                })
            elif lemma.endswith('й'):
                stems.append({
                    'stem': lemma[:-1] + '.',
                    'paradigm': 'Adj-j'
                })
            elif self.rxLastVowel.search(lemma) is not None:
                stems.append({
                    'stem': lemma + '.',
                    'paradigm': 'Adj-vowel'
                })
            else:
                stems.append({
                    'stem': lemma + '.',
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
                    'stem': lemma + '.|' + lemma[-1] + 'ы.|' + lemma[-1] + '.',
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
                    'stem': lemma + '.|' + lemma[-1] + 'ы.|' + lemma[-1] + '.',
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
        return stems, tags

    def fix_tags(self, lang, pos, tags):
        addTags = set()
        delTags = {'poss_yz',
                   'consonant', 'oxyton', 'paroxyton', 'conj_a', 'conj_e',
                   'infl_obl_j', 'infl_obl_k', 'infl_pi', 'infl_v_l'}
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
