import re, collections, csv, requests, tqdm, pickle

class JudgmentsProcessor():

    def __init__(self, raw_judgments, raw_signatures, most_common_words_tagged_file_path, most_common_words_nontagged_file_path):
        self.__raw_judgments__ = raw_judgments
        self.__raw_signatures__ = raw_signatures
        self.__most_common_words_tagged_file_path__ = most_common_words_tagged_file_path
        self.__most_common_words_nontagged_file_path__ = most_common_words_nontagged_file_path
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
        judgments_signatures_after_matching_signatures, not_matching_signatures = self.__match_signatures__(judgments_signatures)
        judgments_signatures = self.__filter_non_matching_codes__(judgments_signatures_after_matching_signatures)
        judgments_categories_counter = self.__count_judgments_categories__(judgments_signatures)
        judgments_signatures = self.__filter_categories_with_few_occurences__(judgments_signatures)
        judgments_signatures = self.__filter__all_decisions_containing_reason__(judgments_signatures)

        tagged_judgments_signatures = []
        non_tagged_judgments_signatures = []
        print ("Before tagging:" + str(len(judgments_signatures)))
        ###############################
        for pair in tqdm.tqdm(judgments_signatures):
            result = self.__make_query_to_tager__(pair)
            if result[0]:
                non_tagged_judgments_signatures.append(pair)
                tagged_judgments_signatures.append(result)
        ###############################
        print ("After tagging:"+ str(len(non_tagged_judgments_signatures)))
        print ("After tagging:" + str(len(tagged_judgments_signatures)))

        print ("Saving judgments to files")

        with open("non_tagged_judgments.pickle", "wb") as file:
            pickle.dump(non_tagged_judgments_signatures, file)

        with open("tagged_judgments_signatures.pickle", "wb") as file:
            pickle.dump(tagged_judgments_signatures, file)

        judgments_categories_counter = self.__count_judgments_categories__(tagged_judgments_signatures)


        most_common_words_tagged = self.__extract_most_common_words__(self.__most_common_words_tagged_file_path__)
        most_common_words_non_tagged = self.__extract_most_common_words__(self.__most_common_words_nontagged_file_path__)

        tagged_judgments_signatures =  self.__remove_most_common_words_from_judgments__(
            tagged_judgments_signatures, most_common_words_tagged)
        non_tagged_judgments_signatures = self.__remove_most_common_words_from_judgments__(
            non_tagged_judgments_signatures, most_common_words_non_tagged)

        X_tagged_tmp, Y_tagged, X_non_tagged_tmp, Y_non_tagged = [], [], [], []
        X_tagged, X_non_tagged = [], []

        for pair in tagged_judgments_signatures:
            X_tagged_tmp.append(pair[0])
            Y_tagged.append(pair[1])

        for sublist in X_tagged_tmp:
            words = " ".join(sublist)
            X_tagged.append(words)

        for pair in non_tagged_judgments_signatures:
            X_non_tagged_tmp.append(pair[0])
            Y_non_tagged.append(pair[1])

        for sublist in X_non_tagged_tmp:
            words = " ".join(sublist)
            X_non_tagged.append(words)

        return X_tagged, Y_tagged, X_non_tagged, Y_non_tagged, judgments_categories_counter

    def __make_query_to_tager__(self, judgment_signature_content):
        data_to_query = (",").join(judgment_signature_content[0])
        r = requests.post(data=data_to_query.encode("utf-8"), url="http://localhost:9200")
        response_text = r.text
        splited_response = response_text.splitlines()
        splited_response = [" ".join(x.replace("\t", " ").replace("none", "")[1:].split(":")[:2][:1]).replace(" ", ":")
                            for x in splited_response if ":" in x]
        splited_response = [x.split(":")[0] for x in splited_response]
        return (splited_response, judgment_signature_content[1])

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

    def __filter_decision_containing_reason__(self, decision):
        try:
            idx = decision.index('uzasadnienie')
            new_decision = decision[idx + 1:]
            new_decision = [word for word in new_decision
                            if (not word.isdigit() and len(word) > 1)]
            return new_decision
        except ValueError:
            return None

    def __filter__all_decisions_containing_reason__(self, judgs_signs):
        filtered_judgments_signatures = []
        for pair in judgs_signs:
            decision = pair[0]
            new_decision = self.__filter_decision_containing_reason__(decision)
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
        print (most_common_words)
        return most_common_words

    def __remove_most_common_words_from_judgments__(self, judgments_signatures, most_common_words_list):
        filtered_judgments = []
        for pair in judgments_signatures:
            judgment = [word for word in pair[0] if word not in most_common_words_list]
            filtered_judgments.append((judgment, pair[1]))
        return filtered_judgments