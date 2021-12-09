import smart_open
from gensim.models import doc2vec
from gensim import utils
from processor import *
from sklearn.linear_model import LogisticRegression


processor = Processor()

tags_index = {
    TAG_TEST_DIR: 0,
    TAG_DIRECTORY: 1,
    TAG_NEGATIVE_CASE: 2
}

tags_bio_index = {
    TAG_TEST_FACULTY: 0,
    TAG_FACULTY: 1,
    TAG_NEGATIVE_CASE_OTHER: 2
}


class Classifier:

    _mode = MODE_TRAIN_MODEL
    _datagen = False
    _task_type = ''
    _tags_dict = {}

    def __init__(self, task_type, train_mode, datagen):
        self._task_type = task_type
        if self._task_type == TASK_DIRECTORY_CLASSIFICATION:
            self._tags_dict = tags_index
        else:
            self._tags_dict = tags_bio_index
        self._mode = MODE_TRAIN_MODEL if train_mode else MODE_LOAD_MODEL
        self._datagen = datagen

    def read_test_corpus(self, file_name, tag_name):
        with smart_open.open(file_name, encoding='iso-8859-1') as f:
            lines = f.readlines()
            for line in lines:
                # preprocess each doc
                tokens = utils.simple_preprocess(line)
                tag_index = [self._tags_dict[tag_name]]
                yield doc2vec.TaggedDocument(tokens[1:], tag_index)

    def read_train_corpus(self, file_name):
        train_corpus = []
        with smart_open.open(file_name, encoding='iso-8859-1') as f:
            lines = f.readlines()
            for line in lines:
                # preprocess each doc
                tokens = utils.simple_preprocess(line)
                tag_name = tokens[0]
                tag_index = [self._tags_dict[tag_name]]
                train_corpus.append(doc2vec.TaggedDocument(tokens[1:], tag_index))
        return train_corpus

    def vector_for_learning(self, model, input_docs):
        tags, feature_vectors = zip(*[(doc.tags[0], model.infer_vector(doc.words, steps=20)) for doc in input_docs])
        return tags, feature_vectors

    def get_key_from_value(self, dictionary, value):
        for k, v in dictionary.items():
            if v == value:
                return k

    def get_doc_from_corpus(self, doc_idx, corpus_file):
        with open(corpus_file, 'r') as f:
            lines = f.readlines()
            return lines[doc_idx][1:]

    def classify_directory_urls(self):
        """
        Train a model with training dataset from known Faculty Directory URLs and non-faculty URLs.
        Classify Faculty Directory URLs from the test dataset using the trained model.
        """
        print "\nAdding label to directory urls ..."

        # read the train corpus
        train_corpus = self.read_train_corpus(TRAIN_DATASET_FILE)

        if self._mode == MODE_LOAD_MODEL and os.path.exists('d2v.model'):
            # load the saved model
            model = doc2vec.Doc2Vec.load('d2v.model')
        else:
            # build and train the model
            model = doc2vec.Doc2Vec(vector_size=100, min_count=2, epochs=50)
            model.build_vocab(train_corpus)
            model.train(train_corpus, total_examples=model.corpus_count, epochs=model.epochs)

            # save the model
            model.save('d2v.model')

        # read the test corpus
        test_corpus = list(self.read_test_corpus(TEST_DATASET_FILE, TAG_TEST_DIR))

        y_train, X_train = self.vector_for_learning(model, train_corpus)
        y_test, X_test = self.vector_for_learning(model, test_corpus)
        logreg = LogisticRegression(solver='liblinear', n_jobs=1, C=1e5)
        logreg.fit(X_train, y_train)
        y_pred = logreg.predict(X_test)

        # now save all the classified directory urls to the file
        with open(CLASSIFIED_DIRECTORY_URLS_FILE, 'w') as fo:
            with open(TEST_URLS_FILE, 'r') as fi:
                lines = fi.readlines()
                for i in range(len(lines)):
                    test_url = lines[i].strip()
                    label = self.get_key_from_value(self._tags_dict, y_pred[i])
                    print "Label: ", label, ", URL: ", test_url
                    if label == TAG_DIRECTORY and self.get_doc_from_corpus(i, TEST_DATASET_FILE) != ERROR_CONTENT:
                        fo.write(test_url)
                        fo.write('\n')

    def classify_faculty_urls(self):
        """
        Train a model with training dataset from known Faculty URLs and non-faculty URLs.
        Classify faculty homepages from the test dataset using the trained model.
        """
        print "\nAdding label to faculty urls ..."

        # read the train corpus
        train_corpus = self.read_train_corpus(TRAIN_BIO_DATASET_FILE)

        if self._mode == MODE_LOAD_MODEL and os.path.exists('d2v-bio.model'):
            # load the saved model
            model = doc2vec.Doc2Vec.load('d2v-bio.model')
        else:
            # build and train the model
            model = doc2vec.Doc2Vec(vector_size=100, min_count=2, epochs=50)
            model.build_vocab(train_corpus)
            model.train(train_corpus, total_examples=model.corpus_count, epochs=model.epochs)

            # save the model
            model.save('d2v-bio.model')

        # read the test corpus
        test_corpus = list(self.read_test_corpus(TEST_BIO_DATASET_FILE, TAG_TEST_FACULTY))

        y_train, X_train = self.vector_for_learning(model, train_corpus)
        y_test, X_test = self.vector_for_learning(model, test_corpus)
        logreg = LogisticRegression(solver='liblinear', n_jobs=1, C=1e5)
        logreg.fit(X_train, y_train)
        y_pred = logreg.predict(X_test)

        # tagged file just for reference
        open('./data/test_bio_urls_tagged.cor', 'w').close()

        with open('./data/test_bio_urls_tagged.cor', 'w') as f2:
            # now save all the classified directory urls to the file
            with open(CLASSIFIED_FACULTY_URLS_FILE, 'w') as fo:
                with open(TEST_BIO_URLS_FILE, 'r') as fi:
                    lines = fi.readlines()
                    for i in range(len(lines)):
                        test_url = lines[i].strip()
                        label = self.get_key_from_value(self._tags_dict, y_pred[i])
                        print "Label: ", label, ", URL: ", test_url
                        if label == TAG_FACULTY and self.get_doc_from_corpus(i, TEST_BIO_DATASET_FILE) != ERROR_CONTENT:
                            fo.write(test_url)
                            fo.write('\n')

                        # also update the tagged file with the final tags
                        f2.write(label + '\t' + test_url)
                        f2.write('\n')
