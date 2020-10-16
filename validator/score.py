from validator.generic import *
from validator.efotrait import EFOTrait

class Score():

    not_null_columns = [
        'name',
        'trait_reported',
        'trait_efo',
        'method_name',
        'variants_number'
    ]

    column_format = {
        'name': 'string',
        'trait_reported': 'string',
        'method_name': 'string',
        'variants_number': 'integer'
    }

    def __init__(self, name, trait_reported, trait_efo, method_name, method_params, variants_number, variants_interactions, variants_genomebuild='NR', trait_additional=None):
        self.name = name
        self.trait_reported = trait_reported
        self.trait_additional = trait_additional
        self.trait_efo = trait_efo
        self.method_name = method_name
        self.method_params = method_params
        self.variants_number =  variants_number
        self.variants_interactions = variants_interactions
        self.variants_genomebuild = variants_genomebuild


    def check_data(self):
        validator = ScoreValidator(self)
        validator.check_not_null()
        validator.check_format()
        return validator.report


class ScoreValidator(GenericValidator):

    def __init__(self, object, type="Score"):
        super().__init__(object,type)
