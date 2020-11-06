from validator.generic import *

class PerformanceMetric():

    def check_data(self, fields_infos, mandatory_fields):
        validator = PerformanceValidator(self, fields_infos, mandatory_fields)
        validator.check_not_null()
        validator.check_format()
        return validator.report


class PerformanceValidator(GenericValidator):

    def __init__(self, object, fields_infos, mandatory_fields, type="Performance"):
        super().__init__(object, fields_infos, mandatory_fields, type)
