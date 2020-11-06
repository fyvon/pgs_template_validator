from validator.generic import *

class Demographic():

    def check_data(self, fields_infos):
        validator = DemographicValidator(self, fields_infos, [])
        validator.check_not_null()
        validator.check_format()
        return validator.report


class DemographicValidator(GenericValidator):

    def __init__(self, object, fields_infos, mandatory_fields, type="Demographic"):
        super().__init__(object, fields_infos, mandatory_fields, type)
