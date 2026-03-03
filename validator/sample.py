from validator.generic import GenericValidator
import logging

class Sample():

    def check_data(self, fields_infos, mandatory_fields):
        validator = SampleValidator(self, fields_infos, mandatory_fields)
        validator.check_not_null()
        validator.check_format()
        validator.check_sample_numbers()
        return validator.report


class SampleValidator(GenericValidator):

    def __init__(self, object, fields_infos, mandatory_fields, type="Sample"):
        super().__init__(object, fields_infos, mandatory_fields, type)


    def check_sample_numbers(self):

        sample_total = None
        if hasattr(self.object, 'sample_number'):
            sample_total = self.object.sample_number

        sample_cases = None
        if hasattr(self.object, 'sample_cases'):
            sample_cases = self.object.sample_cases

        sample_controls = None
        if hasattr(self.object, 'sample_controls'):
            sample_controls = self.object.sample_controls

        sample_percent_male = None
        if hasattr(self.object, 'sample_percent_male'):
            sample_percent_male = self.object.sample_percent_male

        if sample_total:
            try:
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
            except ValueError as e:
                # May happen if value of wrong type (eg: int(not_an_integer)). This type of error is already reported in GenericValidator.check_format().
                # Here we are just preventing the script to crash and allowing it to continue the validation.
                logger = logging.getLogger(__name__)
                logger.error(str(e))
