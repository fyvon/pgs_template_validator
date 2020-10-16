from validator.generic import *

class Demographic():

    not_null_columns = []

    column_format = {
        'estimate': 'float',
        'estimate_type': 'string',
        'unit': 'string',
        'range': '^\d+\.?\d*\s\-\s\d+\.?\d*$',
        'range_type': 'string',
        'variability': 'float',
        'variability_type': 'string',
    }

    def __init__(self, estimate=None, estimate_type=None, unit=None,
                 range=None, range_type=None, variability=None, variability_type=None):
        self.estimate = estimate
        self.estimate_type = type
        self.unit = unit
        self.range = range
        self.range_type = range_type
        self.variability = variability
        self.variability_type = variability_type

    def check_data(self):
        validator = DemographicValidator(self)
        validator.check_not_null()
        validator.check_format()
        return validator.report


class DemographicValidator(GenericValidator):

    def __init__(self, object, type="Demographic"):
        super().__init__(object,type)
