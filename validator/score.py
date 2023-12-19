from validator.generic import GenericValidator
from validator.efotrait import EFOTrait

class Score():

    genomebuilds = ['GRCh37','GRCh38','hg18','hg19','hg38','NCBI35','NCBI36']

    def check_data(self, fields_infos, mandatory_fields):
        validator = ScoreValidator(self, fields_infos, mandatory_fields)
        validator.check_not_null()
        validator.check_format()
        validator.check_value('variants_genomebuild', self.genomebuilds)
        return validator.report


class ScoreValidator(GenericValidator):

    def __init__(self, object, fields_types, mandatory_fields, type="Score"):
        super().__init__(object, fields_types, mandatory_fields, type)
