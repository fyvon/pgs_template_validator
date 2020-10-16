from validator.generic import *

class Sample():

    not_null_columns = [
        'sample_number',
        'ancestry_broad',
    ]

    column_format = {
        'sample_number': 'integer',
        'sample_cases': 'integer',
        'sample_controls': 'integer',
        'sample_percent_male': 'float',
        'phenotyping_free': 'string',
        #'sample_age': 'string',
        #'followup_time': 'string',
        'ancestry_broad': 'string',
        'ancestry_free': 'string',
        'ancestry_country': 'string',
        'ancestry_additional': 'string',
        'source_GWAS_catalog': 'string',
        'source_PMID': 'string',
        'cohorts_additional': 'string'
    }

    def __init__(self, sample_number, ancestry_broad, sample_cases=None, sample_controls=None, sample_percent_male=None,
                phenotyping_free=None, followup_time=None, sample_age=None, ancestry_free=None, ancestry_country=None,
                ancestry_additional=None, source_GWAS_catalog=None, source_PMID=None, cohorts=[], cohorts_additional=None):
        self.sample_number = sample_number
        self.sample_cases = sample_cases
        self.sample_controls = sample_controls
        self.sample_percent_male = sample_percent_male
        self.phenotyping_free = phenotyping_free
        self.followup_time = followup_time
        self.sample_age = sample_age
        self.ancestry_broad = ancestry_broad
        self.ancestry_free = ancestry_free
        self.ancestry_country = ancestry_country
        self.ancestry_additional = ancestry_additional
        self.source_GWAS_catalog = source_GWAS_catalog,
        self.source_PMID = source_PMID
        self.cohorts = cohorts
        self.cohorts_additional = cohorts_additional


    def check_data(self):
        validator = SampleValidator(self)
        validator.check_not_null()
        validator.check_format()
        if self.sample_age:
            sample_age_check_report = self.sample_age.check_data()
            if len(sample_age_check_report) > 0:
                for check_report in sample_age_check_report:
                    validator.report.append(check_report)
        if self.followup_time:
            followup_time_check_report = self.followup_time.check_data()
            if len(followup_time_check_report) > 0:
                for check_report in followup_time_check_report:
                    validator.report.append(check_report)
        return validator.report


class SampleValidator(GenericValidator):

    def __init__(self, object, type="Sample"):
        super().__init__(object,type)
