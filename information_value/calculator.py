# This Python file uses the following encoding: utf-8
from __future__ import division
from copy import deepcopy
from random import shuffle
import math
import random
import operator
import nltk


def print_probabilty(str, prob):
    if random.random() < prob:
        print str


def get_count(ctuple):
    return ctuple[1]


class WindowSizeTooLarge(Exception):
    pass


class InformationValueCalculator:

    def __init__(self, tokens):
        #se carga la lista de tokens
        self.tokens = tokens
        self.randomized_text = deepcopy(self.tokens)
        shuffle(self.randomized_text)
        self.word_fdist = nltk.FreqDist(self.tokens)

    def number_of_windows(self, window_size):
        return int(math.ceil(self.word_fdist.N() / window_size))

    def get_frequencies(self, tokenized_text, window_size):
        freq = dict((word, []) for word in self.word_fdist.samples())
        P = self.number_of_windows(window_size)
        for i in range(0, P):
            window = get_window(tokenized_text, window_size=window_size, number_of_window=i)
            window_fdist = nltk.FreqDist(window)

            for word in self.word_fdist.samples():
                freq[word].append(window_fdist.freq(word))

        return freq

    def occurrence_probability(self, window_size, tokenized_text):
        P = self.number_of_windows(window_size)
        if P == 0 or P == 1:
            raise WindowSizeTooLarge("Ventana de tamaño %s para texto de tamaño %s" % (window_size, self.word_fdist.N()))

        freq = self.get_frequencies(tokenized_text, window_size)
        sum_f = dict((word, sum(freq[word])) for word in self.word_fdist.samples())

        p = {}
        for word in self.word_fdist.samples():
            p[word] = []
            for i in range(0, P):
                if sum_f[word] != 0:
                    p[word].append(freq[word][i] / sum_f[word])
                else:
                    p[word].append(.0)
        return p

    def entropy(self, tokenized_text, window_size):
        p = self.occurrence_probability(window_size, tokenized_text)
        if not p:
            return False
        S = {}
        P = self.number_of_windows(window_size)

        for word in self.word_fdist.samples():
            S[word] = 0
            for prob in p[word]:
                if prob:
                    S[word] = S[word] + (prob * math.log(prob))
            S[word] = (-1) * S[word] / math.log(P)
        return S

    #Calcular la "information value" de las palabras seleccionadas,
    #Definicion de IV:
    # "The difference between the two entropies multiplied by the frequency of the word gives
    # the word’s 'information value' in the text.
    # Information value, just as in binary computing, is measured in bits."

    def information_value(self, window_size):
        ordered_entropy = self.entropy(self.tokens, window_size)

        random_entropy = self.entropy(self.randomized_text, window_size)

        information_value_per_word = {}
        for word in self.word_fdist.samples():
            freq = self.word_fdist.freq(word)
            information_value_per_word[word] = freq * abs(ordered_entropy[word] - random_entropy[word])

        return information_value_per_word


def get_window(tokens, window_size, number_of_window):
    from information_value.window import Window
    return Window(tokens, window_size, number_of_window)
