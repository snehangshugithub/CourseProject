import shutil
from crawler import *

BIO_URLS_SPLIT_POINT = 1000

NEGATIVE_CASE_BIO_URLS_SAMPLE_SIZE = 20

class Processor:

    def build_faculty_urls(self, file_name, corpus_type):
        """
        Build the faculty directory urls from the MP 2.1 sign up sheet csv
        """
        print "\nCreating faculty directory urls ..."
        tmp_file = os.path.join(os.path.dirname(file_name), 'tmp_' + os.path.basename(file_name))
        if not os.path.exists(tmp_file):
            open(tmp_file, 'w').close()

        with open(tmp_file, 'w') as fo:
            with open(file_name, 'r') as fi:
                lines = fi.readlines()
                for line in lines:
                    parts = line.split(',')
                    last_part = parts[-1]
                    if last_part and last_part != '"' and last_part != '\r' and last_part != '\n' and last_part != '\r\n':
                        if not (last_part.startswith('"') and not last_part.endswith('"')):
                            if re.findall("\.", last_part):
                                data_string = ""
                                if corpus_type == DATA_TYPE_TRAINING:
                                    data_string += TAG_DIRECTORY + '\t'
                                data_string += parts[-1]
                                fo.write(data_string)

        cleaned_data_file = os.path.splitext(file_name)[0] + '.cor'
        shutil.move(tmp_file, cleaned_data_file)

    def build_negative_case_train_urls(self):
        """
        Build the negative_case train urls set from the country specific negative_case urls
        """
        print "\nCreating negative_case train urls ..."
        # negative test case sample
        negative_case_train_files = ['./data/original/Negative_case_set_1.cor', './data/original/Negative_case_set_2.cor']
        unique_urls = set([])

        for train_file in negative_case_train_files:
            with open(train_file, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    unique_urls.add(line)

        # Populate the negative_case training urls file
        if not os.path.exists(NEGATIVE_CASE_TRAIN_URLS_FILE):
            open(NEGATIVE_CASE_TRAIN_URLS_FILE, 'w').close()

        with open(NEGATIVE_CASE_TRAIN_URLS_FILE, 'w') as f:
            for url in unique_urls:
                data_string = TAG_NEGATIVE_CASE + '\t' + url
                f.write(data_string)

    def build_negative_case_test_urls(self):
        """
        Build the negative_case test urls set from the country specific negative_case urls
        """
        print "\nCreating negative_case test urls ..."
        # negative test case sample
        negative_case_test_files = ['./data/original/Negative_case_set_3.cor', './data/original/Negative_case_set_4.cor']
        with open(NEGATIVE_CASE_TRAIN_URLS_FILE, 'r') as f:
            negative_case_train_urls = f.readlines()

        # Unique negative_case test urls excluding any urls in the negative_case training urls
        unique_urls = set([])

        for test_file in negative_case_test_files:
            with open(test_file, 'r') as f:
                test_urls = f.readlines()
                for test_url in test_urls:
                    if test_url not in negative_case_train_urls:
                        unique_urls.add(test_url)

        # Populate the negative_case test urls file
        if not os.path.exists(NEGATIVE_CASE_TEST_URLS_FILE):
            open(NEGATIVE_CASE_TEST_URLS_FILE, 'w').close()

        with open(NEGATIVE_CASE_TEST_URLS_FILE, 'w') as f:
            for url in unique_urls:
                f.write(url)

    def mix_train_urls(self):
        """
        Mix the urls from negative_case url train set and faculty directory url train set
        """
        print "\nMixing train urls ..."
        unique_urls = set([])
        with open(NEGATIVE_CASE_TRAIN_URLS_FILE, 'r') as f:
            lines = f.readlines()
            for line in lines:
                unique_urls.add(line)

        with open(FACULTY_DIR_TRAIN_URLS_FILE, 'r') as f:
            lines = f.readlines()
            for line in lines:
                unique_urls.add(line)

        if not os.path.exists(TRAIN_URLS_FILE):
            open(TRAIN_URLS_FILE, 'w').close()

        with open(TRAIN_URLS_FILE, 'w') as f:
            for url in unique_urls:
                f.write(url)

    def mix_test_urls(self):
        """
        Mix the urls from negative_case url test set and faculty directory url test set
        """
        print "\nMixing test urls ..."
        unique_urls = set([])
        with open(NEGATIVE_CASE_TEST_URLS_FILE, 'r') as f:
            lines = f.readlines()
            for line in lines:
                unique_urls.add(line)

        with open(FACULTY_DIR_TEST_URLS_FILE, 'r') as f:
            lines = f.readlines()
            for line in lines:
                unique_urls.add(line)

        if not os.path.exists(TEST_URLS_FILE):
            open(TEST_URLS_FILE, 'w').close()

        with open(TEST_URLS_FILE, 'w') as f:
            for url in unique_urls:
                f.write(url)

    def prepare_data_source(self):
        """
        Prepare the train and test urls for the directory url classification task
        """
        print "\nCreating faculty directory urls from both sources ..."
        self.build_faculty_urls("./data/original/Faculty_Directory_Train.csv", DATA_TYPE_TRAINING)
        self.build_negative_case_train_urls()
        self.mix_train_urls()

        self.build_faculty_urls("./data/original/Faculty_Directory_Test.csv", DATA_TYPE_TESTING)
        self.build_negative_case_test_urls()
        self.mix_test_urls()

    def prepare_corpus(self, corpus_type):
        """
        Prepare the corpus for the directory url classification task
        """
        print "\nCreating corpus of directory urls for {} ...".format(corpus_type)
        crawler = Crawler(corpus_type)
        crawler.create_output_file()
        crawler.extract_url_contents()

    def prepare_train_bio_data_source(self):
        """
        Prepare the urls file for training the bio classifier
        """
        print "\nCreating train bio urls ..."
        if not os.path.exists(TRAIN_BIO_URLS_FILE):
            open(TRAIN_BIO_URLS_FILE, 'w').close()

        this_file_dir = os.path.dirname(os.path.abspath(__file__))
        existing_bio_urls_file = os.path.join(os.path.dirname(this_file_dir), 'data/urls')
        # "CourseProject/ExpertSearch/data/urls"
        with open(TRAIN_BIO_URLS_FILE, 'w') as fo:
            # take the first 1000 urls as training data
            with open(existing_bio_urls_file, 'r') as fi:
                lines = fi.readlines()
                for i in range(BIO_URLS_SPLIT_POINT):
                    faculty_bio_url = lines[i].strip()
                    fo.write(TAG_FACULTY + '\t' + faculty_bio_url)
                    fo.write('\n')

        with open(TRAIN_BIO_URLS_FILE, 'a') as fo:
            # negative test case sample
            negative_case_test_files = ['./data/original/Negative_case_set_3.cor', './data/original/Negative_case_set_4.cor']
            test_urls = set([])
            for test_file in negative_case_test_files:
                with open(test_file, 'r') as fi:
                    test_file_urls = fi.readlines()
                    test_urls.update(test_file_urls)

            for url in test_urls:
                url = url.strip()
                if not self.is_non_ascii(url):
                    fo.write(TAG_NEGATIVE_CASE_OTHER + '\t' + url)
                    fo.write('\n')

    def prepare_train_bio_corpus(self):
        """
        Prepare the bio corpus for training the bio classifier
        """
        print "\nCreating train bio corpus ..."
        crawler = Crawler(DATA_TYPE_BIO_TRAINING)
        crawler.create_output_file()

        # The first 2000 urls are from the existing bio urls,
        # so copy their corresponding bio file contents to our output file
        this_file_dir = os.path.dirname(os.path.abspath(__file__))
        with open(TRAIN_BIO_DATASET_FILE, 'w') as fo:
            for i in range(BIO_URLS_SPLIT_POINT):
                # "CourseProject/ExpertSearch/data/compiled_bios/6524.txt"
                bio_file_name = str(i) + '.txt'
                existing_bio_file = os.path.join(os.path.dirname(this_file_dir), 'data/compiled_bios', bio_file_name)
                with open(existing_bio_file, 'r') as fi:
                    bio_text = fi.readlines()[0].strip()
                    fo.write(TAG_FACULTY + '\t' + bio_text)
                    fo.write('\n')

        # For the remaining urls, extract the content from TRAIN_BIO_URLS_FILE and write to the output file
        crawler.extract_url_contents(start_idx=BIO_URLS_SPLIT_POINT)

    def prepare_test_bio_data_source(self):
        """
        Prepare the urls file (TEST_BIO_URLS_FILE) for testing the bio classifier
        """
        print "\nCreating test bio urls ..."
        if not os.path.exists(TEST_BIO_URLS_FILE):
            open(TEST_BIO_URLS_FILE, 'w').close()

        # Prepare the test bio URLs file
        with open(TEST_BIO_URLS_FILE, 'w') as fo:
            # Use the classified directory URLs to find faculty bio URLs and use as test URLs
            with open(CLASSIFIED_DIRECTORY_URLS_FILE, 'r') as fi:
                lines = fi.readlines()
                for i, line in enumerate(lines):
                    test_url = line.strip()
                    crawler = Crawler(DATA_TYPE_BIO_TESTING)
                    # Get all potential faculty bio URLs from each directory URL
                    test_sub_urls = crawler.get_links_from_url(test_url)
                    for j, test_sub_url in enumerate(test_sub_urls):
                        if not self.is_non_ascii(test_sub_url):
                            fo.write(test_sub_url.strip())
                            fo.write('\n')

    def prepare_test_bio_corpus(self):
        """
        Prepare the bio corpus for testing the bio classifier
        """
        print "\nCreating test bio corpus ..."
        crawler = Crawler(DATA_TYPE_BIO_TESTING)
        crawler.create_output_file()
        crawler.extract_url_contents()

    def is_non_ascii(self, string):
        for c in string:
            if ord(c) >= 128:
                return True
        return False
