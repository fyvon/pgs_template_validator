from validator.generic import *
from validator.efotrait import EFOTrait

class Score():

    def check_data(self, fields_infos, mandatory_fields):
        validator = ScoreValidator(self, fields_infos, mandatory_fields)
        validator.check_not_null()
        validator.check_format()
        return validator.report


class ScoreValidator(GenericValidator):

    def __init__(self, object, fields_types, mandatory_fields, type="Score"):
        super().__init__(object, fields_types, mandatory_fields, type)
