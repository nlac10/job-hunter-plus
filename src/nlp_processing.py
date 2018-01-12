import pandas as pd
import numpy as np
from .utils import get_stopwords
from .dataframe_processing import create_model_data
from nltk.stem.porter import PorterStemmer
from nltk.stem.snowball import SnowballStemmer
from nltk.stem.wordnet import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer


class NLPProcessing:
    """
    Provides methods for transforming text data.
    """

    def __init__(self, stemlem="", min_df=1, max_df=1.0, num_cities=2,
                 n_grams=1, use_stopwords=True):
        """
        Instantiate the preprocessing class.
        :param stemlem: str or list, stemmatizer or lemmatizer to use.
        :param num_cities: int, the number of cities to retain.
        :param min_df: float or int, minimum document frequency of term.
        :param max_df: float or int, maximum document frequency of term.
        :param n_grams: int, n-gram to use
        :param use_stopwords: bool, whether to use stopwords or not
        """
        self.model = None
        self.stemlem = stemlem
        self.min_df = min_df
        self.max_df = max_df
        self.num_cities = num_cities
        self.vectorize = None
        self.n_grams = n_grams
        self.use_stopwords = use_stopwords
        self.done_stopwords = False

    def fit(self, data=None, bucket=None, filename=None):
        """
        Single function to fit the NLP transformations.
        Uses a user defined stemmer/lemmatizer with TFIDF vectorization.
        :param data: Pandas DataFrame containing data.
        :param bucket: str S3 bucket of data if applicable.
        :param filename: str, name of the data file, if applicable.
        """
        fit_array, _, _ = create_model_data(data, bucket, filename, self.num_cities)
        fit_array = self._stemlem(fit_array)
        self.tfidf_vectorize(fit_array)

    def transform(self, data=None, bucket=None, filename=None):
        """
        Single function to apply the NLP transformation.
        :param data: Pandas DataFrame containing data.
        :param bucket: str S3 bucket of data if applicable.
        :param filename: str, name of the data file, if applicable.
        :return: ndarrays for the feature and label matrices
        """
        if self.vectorize is None:
            raise AttributeError("Must fit a processing pipeline before calling\
                                 the transform method")
        _, doc_array, y = create_model_data(data, bucket, filename,
                                            self.num_cities)
        doc_array = self._stemlem(doc_array)
        x = self.vectorize.transform(doc_array)
        return x, y

    def fit_transform(self, data=None, bucket=None, filename=None):
        """
        Single function to fit model and apply it in one go.
        :param data: Pandas DataFrame containing data.
        :param bucket: str S3 bucket of data if applicable.
        :param filename: str, name of the data file, if applicable.
        :return: ndarrays for the feature and label matrices
        """
        fit_array, doc_array, y = create_model_data(data, bucket, filename,
                                                    self.num_cities)
        fit_array = self._stemlem(fit_array)
        self.tfidf_vectorize(fit_array)
        doc_array = self._stemlem(doc_array)
        x = self.vectorize.transform(doc_array)
        return x, y

    def _stemlem(self, text_array):
        """
        Controls the stemmatization/lemmatization process.
        Note that, if multiple methods are selected, lemmatization is performed
        before stemmatization.
        :param text_array: ndarray, the documents to process.
        :return: ndarray, the processed documents
        """
        self.done_stopwords = True
        if "wordnet" in self.stemlem:
            text_array = self.wordnet_lemmatizer(text_array)
        if "snowball" in self.stemlem:
            text_array = self.snowball_stemmatizer(text_array)
        elif "porter" in self.stemlem:
            text_array = self.porter_stemmatizer(text_array)
        if self.stemlem == "":
            text_array = list(text_array)
        self.done_stopwords = False
        return text_array

    def snowball_stemmatizer(self, documents):
        """
        Apply the snowball stemmatizer to the job description text.
        """
        return self._do_stem_lem(documents, SnowballStemmer("english"), True)

    def porter_stemmatizer(self, documents):
        """
        Apply the Porter stemmatizer to the job description text.
        """
        return self._do_stem_lem(documents, PorterStemmer(), True)

    def wordnet_lemmatizer(self, documents):
        """
        Apply the WordNet lemmatizer to the job description text.
        """
        return self._do_stem_lem(documents, WordNetLemmatizer(), False)

    def _do_stem_lem(self, documents, model, stemmer):
        """
        Actually perform the stemming / lemmatizing and stop word removal.
        :param documents: the list of documents to transform.
        :param model: the instantiated transformation to use.
        :param stemmer: bool, True for stemming, False for lemmatizing.
        :return: list, the transformed documents
        """
        stop_words = set()
        if self.use_stopwords and not self.done_stopwords:
            stop_words = get_stopwords()
        if stemmer:
            return [" ".join([model.stem(word) for word in text.split(" ")
                              if word not in stop_words])
                    for text in documents]
        else:
            return [" ".join([model.lemmatize(word) for word in text.split(" ")
                              if word not in stop_words])
                    for text in documents]

    def count_vectorize(self, training_docs):
        """
        Vectorize the corpus using bag of words vectorization
        :param training_docs: Numpy array, the text to fit the vectorizer
        :return: SK Learn vectorizer object
        """
        stop_words = set()
        if self.use_stopwords and self.stemlem == "":
            stop_words = get_stopwords()
        # Instantiate class and fit vocabulary
        self.vectorize = CountVectorizer(training_docs, stop_words=stop_words,
                                         min_df=self.min_df, max_df=self.max_df)
        self.vectorize.fit(training_docs)

    def tfidf_vectorize(self, training_docs):
        """
        Vectorize the corpus using TFIDF vectorization
        :param training_docs: Numpy array, the text to fit the vectorizer
        :return: SK Learn vectorizer object
        """
        stop_words = set()
        if self.use_stopwords and self.stemlem == "":
            stop_words = get_stopwords()
        # Instantiate class and fit vocabulary
        self.vectorize = TfidfVectorizer(training_docs, stop_words=stop_words,
                                         min_df=self.min_df, max_df=self.max_df,
                                         ngram_range=(self.n_grams, self.n_grams))
        self.vectorize.fit(training_docs)
