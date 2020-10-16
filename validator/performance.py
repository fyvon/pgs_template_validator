from validator.generic import *

class PerformanceMetric():

    not_null_columns = [
        'score_name',
        'sampleset',
        'phenotyping_reported',
        'metrics'
    ]

    column_format = {
        'score_name': 'string',
        'sampleset': 'string',
        'phenotyping_reported': 'string',
        'covariates': 'string',
        'performance_comments': 'string',
    }

    def __init__(self, score_name, sampleset, phenotyping_reported, metrics, covariates=None, performance_comments=None):
        self.score_name = score_name
        self.sampleset = sampleset
        self.phenotyping_reported = phenotyping_reported
        self.metrics = metrics
        self.covariates = covariates
        self.performance_comments = performance_comments

    def check_data(self):
        validator = PerformanceValidator(self)
        validator.check_not_null()
        validator.check_format()
        for metric in self.metrics:
            metric_check_report = metric.check_data()
            if len(metric_check_report) > 0:
                for check_report in metric_check_report:
                    validator.report.append(check_report)
        return validator.report


class PerformanceValidator(GenericValidator):

    def __init__(self, object, type="Performance"):
        super().__init__(object,type)
