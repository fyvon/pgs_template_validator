from validator.generic import *

class Metric():

    not_null_columns = [
        'name',
        'name_short',
        'type',
        'estimate'
    ]

    column_format = {
        'name': 'string',
        'name_short': 'string',
        'type': 'string',
        'estimate': 'float',
        'unit': 'string',
        'se': 'float',
        'ci': '^\d+\.?\d*\s\-\s\d+\.?\d*$'
    }

    def __init__(self, name, name_short, type, estimate, unit=None, se=None, ci=None):
        self.name = name
        self.name_short = name_short
        self.type = type
        self.estimate = estimate
        self.unit = unit
        self.se = se
        self.ci = ci

    def check_data(self):
        validator = MetricValidator(self)
        validator.check_not_null()
        validator.check_format()
        return validator.report


class MetricValidator(GenericValidator):

    def __init__(self, object, type="Metric"):
        super().__init__(object,type)
