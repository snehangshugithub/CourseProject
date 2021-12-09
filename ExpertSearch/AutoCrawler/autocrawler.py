import argparse
from classifier import *

processor = Processor()

def prep_data_for_dir_classification():
    open(CLASSIFIED_DIRECTORY_URLS_FILE, 'w').close()

    processor.prepare_data_source()
    processor.prepare_corpus(DATA_TYPE_TRAINING)
    processor.prepare_corpus(DATA_TYPE_TESTING)

def prep_data_for_bio_classification():
    open(CLASSIFIED_FACULTY_URLS_FILE, 'w').close()

    processor.prepare_train_bio_data_source()
    processor.prepare_train_bio_corpus()
    processor.prepare_test_bio_data_source()
    processor.prepare_test_bio_corpus()

def main():

    gen_data = True
    train_model = True

    # add new training and test data if gen_data is true or if the dataset doesn't exist yet
    if gen_data or not (os.path.exists(TRAIN_DATASET_FILE) or os.path.exists(TEST_DATASET_FILE)):
        prep_data_for_dir_classification()

    # classify the directory urls from the test dataset
    classifier = Classifier(TASK_DIRECTORY_CLASSIFICATION, train_model, gen_data)
    classifier.classify_directory_urls()

    # add new training and test bio data if gen_data is true or if the dataset doesn't exist yet
    if gen_data or not (os.path.exists(TRAIN_BIO_DATASET_FILE) or os.path.exists(TEST_BIO_DATASET_FILE)):
        prep_data_for_bio_classification()

    # classify the faculty urls from the test dataset
    classifier = Classifier(TASK_FACULTY_CLASSIFICATION, train_model, gen_data)
    classifier.classify_faculty_urls()

    # now crawl the bios from each classified faculty url from the file CLASSIFIED_FACULTY_URLS_FILE
    # and save each individual bio file under the compiled_bios folder
    crawler = Crawler(DATA_TYPE_BIO_TESTING)
    crawler.crawl_faculty_pages_for_bio()

    # Also, append the new faculty urls to the data/urls file
    crawler.add_classified_fac_url_to_urls()

if __name__ == '__main__':
    # Run it as:
    main()
