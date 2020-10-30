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
        validator.check_sample_numbers()
        if self.sample_age:
            sample_age_check_report = self.sample_age.check_data()
            if len(sample_age_check_report['error']) > 0:
                for check_report in sample_age_check_report['error']:
                    validator.add_error_report(check_report)
            if len(sample_age_check_report['warning']) > 0:
                for check_report in sample_age_check_report['warning']:
                    validator.add_warning_report(check_report)
        if self.followup_time:
            followup_time_check_report = self.followup_time.check_data()
            if len(followup_time_check_report['error']) > 0:
                for check_report in followup_time_check_report['error']:
                    validator.add_error_report(check_report)
            if len(followup_time_check_report['warning']) > 0:
                for check_report in followup_time_check_report['warning']:
                    validator.add_warning_report(check_report)
        return validator.report


class SampleValidator(GenericValidator):

    def __init__(self, object, type="Sample"):
        super().__init__(object,type)


    def check_sample_numbers(self):

        sample_total = self.object.sample_number
        sample_cases = self.object.sample_cases
        sample_controls = self.object.sample_controls
        sample_percent_male = self.object.sample_percent_male
        if sample_total:
            sample_total = int(sample_total)
            if sample_total == 0:
                self.add_error_report("The total number of Samples is equals to 0. The minimum value should be 1.")
            if sample_cases:
                sample_cases = int(sample_cases)
                if sample_cases == 0:
                    self.add_error_report("The number of Samples cases is equals to 0. The minimum value should be 1.")
                if sample_cases > sample_total:
                    self.add_error_report(f'The number of Samples cases ({sample_cases}) is greater than the total number of Samples ({sample_total})')
            if sample_controls:
                sample_controls = int(sample_controls)
                if sample_controls > sample_total:
                    self.add_error_report(f'The number of Samples controls ({sample_controls}) is greater than the total number of Samples ({sample_total})')
            if sample_cases and sample_controls:
                combined_samples = sample_cases + sample_controls
                if combined_samples > sample_total:
                    self.add_error_report(f'The combined numbers of Samples cases and controls ({sample_cases} + {sample_controls} = {combined_samples}) is greater than the total number of Samples ({sample_total})')
            if sample_percent_male and (isinstance(sample_percent_male, int) or isinstance(sample_percent_male, float)):
                sample_percent_male = float(sample_percent_male)
                if sample_percent_male < 0 or sample_percent_male > 100:
                    self.add_error_report(f'The percentage should be between 0 and 100.')
                if 0 < sample_percent_male < 1:
                    self.add_warning_report(f'The percentage should be between 0 and 100. Make sure that the value is supposed to be ###% and not ###*100%.')
