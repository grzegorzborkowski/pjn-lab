import re, collections, csv

class JudgmentsProcessor():

    def __init__(self, raw_judgments, raw_signatures, most_common_words_file_path, tagger_broken_list = []):
        self.__raw_judgments__ = raw_judgments
        self.__raw_signatures__ = raw_signatures
        self.__most_common_words_file_path__ = most_common_words_file_path
        self.__tagger_broken_list__ = tagger_broken_list
        self.__signatures_regexes__ = {
            re.compile(r'A?C.*'): 'sprawy cywilne',
            re.compile(r'A?U.*'): 'sprawy z zakresu ubezpieczenia społecznego',
            re.compile(r'A?K.*'): 'sprawy karne',
            re.compile(r'G.*'): 'sprawy gospodarcze',
            re.compile(r'A?P.*'): 'sprawy w zakresie prawa pracy',
            re.compile(r'R.*'): 'sprawy w zakresie prawa rodzinnego',
            re.compile(r'W.*'): 'sprawy o wykroczenia',
            re.compile(r'Am.*'): 'sprawy w zakresie prawa konkurencji'
        }

    def process_judgments(self):
        '''
        Transforms judgments and signatures, removing obsolete words,
        matching signatures codes to signatures regex map,
        removing most common words from judgments texts and removing underrepresented signatures
        :return:
        X, Y: X is a list of judgments texts, Y is a list of corresponding signatures
        '''
        signatures_categories = self.__extract_signatures_categories__()
        judgments_signatures = list(zip(self.__raw_judgments__, signatures_categories))

        # print ("Content before filter_based_on_tagger_list" + str(((judgments_signatures)[:10])))
        # judgments_signatures = self.__filter_based_on_tagger_list__(judgments_signatures)
        # print ("Content after filter based on tagger list" + str(judgments_signatures))
        judgments_signatures_after_matching_signatures, not_matching_signatures = self.__match_signatures__(judgments_signatures)
        judgments_signatures = self.__filter_non_matching_codes__(judgments_signatures_after_matching_signatures)
        judgments_categories_counter = self.__count_judgments_categories__(judgments_signatures)
        judgments_signatures = self.__filter_categories_with_few_occurences__(judgments_signatures)
        most_common_words = self.__extract_most_common_words__(self.__most_common_words_file_path__)
        judgments_signatures = self.__filter__all_decisions__(judgments_signatures, most_common_words)

        X, Y, new_X = [], [], []

        for pair in judgments_signatures:
            X.append(pair[0])
            Y.append(pair[1])

        for sublist in X:
            words = " ".join(sublist)
            new_X.append(words)

        return new_X, Y

    def __extract_signatures_categories__(self):
        signatures_flatten = [item for sublist in self.__raw_signatures__ for item in sublist]
        signatures_categories = []
        for signature in signatures_flatten:
            splited = signature.split(" ")
            signatures_categories.append(splited[1])
        return signatures_categories

    def __match_signatures_to_code__(self, code):
        for judg_regex in self.__signatures_regexes__.keys():
            if (re.match(judg_regex, code)):
                return self.__signatures_regexes__[judg_regex]
        return None

    def __match_signatures__(self, judgments_and_signatures_list):
        judgments_and_signatures_list_after_transformation = []
        not_matching_signatures = []
        for pair in judgments_and_signatures_list:
            code = pair[1]
            res = self.__match_signatures_to_code__(code)
            judgments_and_signatures_list_after_transformation.append((pair[0], res))
            if res is None:
                not_matching_signatures.append(code)
        return judgments_and_signatures_list_after_transformation, not_matching_signatures

    def __filter_non_matching_codes__(self, judgments_and_signatures_list):
        result = list(filter(lambda x: x[1] is not None,
                                           judgments_and_signatures_list))
        return result

    def __count_judgments_categories__(self, judgments_signatures):
        cases_types = [case[1] for case in judgments_signatures]
        cases_type_counter = collections.Counter(cases_types)
        return cases_type_counter

    def __filter_categories_with_few_occurences__(self, judgments_signatures):
        filtered_judgments_signatures = []
        for pair in judgments_signatures:
            if pair[1] != 'sprawy w zakresie prawa konkurencji':
                filtered_judgments_signatures.append(pair)
        return filtered_judgments_signatures

    def __filter_decision__(self, decision, most_common_words):
        try:
            idx = decision.index('uzasadnienie')
            new_decision = decision[idx + 1:]
            new_decision = [word for word in new_decision
                            if (not word.isdigit() and len(word) > 1 and word not in most_common_words)]
            return new_decision
        except ValueError:
            pass

    def __filter__all_decisions__(self, judgs_signs, most_common_words):
        filtered_judgments_signatures = []
        for pair in judgs_signs:
            decision = pair[0]
            new_decision = self.__filter_decision__(decision, most_common_words)
            if new_decision:
                filtered_judgments_signatures.append((new_decision, pair[1]))
        return filtered_judgments_signatures

    def __extract_most_common_words__(self, path):
        most_common_words = []
        with open(path) as file:
            idx, number_of_rows = 0, 20
            csv_reader = csv.reader(file)
            for row in csv_reader:
                word = ",".join(row).split(",")[1]
                most_common_words.append(word)
                idx += 1
                if idx >= number_of_rows:
                    break
        return most_common_words

    def __filter_based_on_tagger_list__(self, judgments_signature_list):
        print ("tagger_broken_list" + str(self.__tagger_broken_list__))
        print ("judgments_signature_list" + str(list(judgments_signature_list)))

        if len(self.__tagger_broken_list__) != len(judgments_signature_list):
            return judgments_signature_list
        print ("Filtering!")
        zipped = list(zip(judgments_signature_list, self.__tagger_broken_list__))
        return list(filter(lambda x: x[1] is True, zipped))
