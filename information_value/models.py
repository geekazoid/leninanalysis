# coding: utf-8
import logging
import hashlib

from pymongo.errors import DuplicateKeyError

from ming import Session, create_datastore
from ming import schema
from ming.odm import ODMSession
from ming.odm.mapper import MapperExtension
from ming.odm.property import ForeignIdProperty
from ming.odm.property import FieldProperty, RelationProperty
from ming.odm.declarative import MappedClass

import config
from includes.tokenizer import tokenize


log = logging.getLogger('lenin')

bind = create_datastore(config.DATABASE_NAME)
session = Session(bind)
odm_session = ODMSession(doc_session=session)


class DocumentWindowSizeDuplicateHash(MapperExtension):
    """
        Used as unique key for Document - WindowSize
    """
    def before_insert(self, instance, state, session):
        doc_window_hash = hashlib.sha1(str(instance.document_id) + str(instance.window_size)).hexdigest()
        if instance.__class__.query.find({'doc_window_hash': doc_window_hash}).count() > 0:
            raise DuplicateKeyError('Duplicate hash found ', doc_window_hash)
        instance.doc_window_hash = doc_window_hash


class Document(MappedClass):

    class __mongometa__:
        session = odm_session
        name = 'document'

    _id = FieldProperty(schema.ObjectId)
    url = FieldProperty(schema.String, unique=True)
    name = FieldProperty(schema.String)
    text = FieldProperty(schema.String)
    month = FieldProperty(schema.String)
    year = FieldProperty(schema.Int)
    results = RelationProperty('InformationValueResult')

    def get_information_value_result(self, threshold):
        iv_res = None
        best_iv = 0.0
        total_words = len(self.tokens)
        take_words = int(threshold * total_words)

        for one_iv in self.results:
            sum_iv = sum(map(lambda (w, iv): iv ,one_iv.iv_words[:take_words]))
            if best_iv <= sum_iv:
                best_iv = sum_iv
                iv_res = one_iv
        return iv_res

    @property
    def tokens(self):
        tokenizer_func = getattr(self, 'tokenizer', tokenize)
        return tokenizer_func(self.text)


class InformationValueResult(MappedClass):

    class __mongometa__:
        session = odm_session
        name = 'information_value_result'
        unique_indexes = [('doc_window_hash', ), ]
        extensions = [DocumentWindowSizeDuplicateHash]

    _id = FieldProperty(schema.ObjectId)
    doc_window_hash = FieldProperty(schema.String)
    window_size = FieldProperty(schema.Int)
    iv_words = FieldProperty(schema.Anything)
    document_id = ForeignIdProperty(Document)
    document = RelationProperty(Document)
