from validator.generic import GenericValidator

class Metric():

    def check_data(self, fields_infos):
        mandatory_fields = [
            'name',
            'name_short',
            'type',
            'estimate'
        ]
        validator = MetricValidator(self, fields_infos, mandatory_fields)
        validator.check_not_null()
        validator.check_format()
        return validator.report


class MetricValidator(GenericValidator):

    def __init__(self, object, fields_infos, mandatory_fields, type="Metric"):
        super().__init__(object, fields_infos, mandatory_fields, type)
