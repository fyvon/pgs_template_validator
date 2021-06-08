import os, sys, glob, re
import argparse
from validator.main_validator import PGSMetadataValidator

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-f", help='The path to the PGS Catalog metadata file to be validated', required=True, metavar='PGS_METADATA_FILE_NAME')
    argparser.add_argument("-r", help='Flag to indicate if the file is remote (accessible via the Google Cloud Storage)')

    args = argparser.parse_args()

    # Check study file exists
    metadata_filename = args.f
    metadata_is_remote = False
    if args.r:
        metadata_is_remote = True
    if not metadata_is_remote:
        if not os.path.isfile(metadata_filename):
            print("File '"+metadata_filename+"' can't be found")
            exit(1)

    expected_file_extension = 'xlsx'
    filename = os.path.basename(metadata_filename)
    extension = filename.split('.')[-1]
    if extension != expected_file_extension:
         print(f'The expected file extension is [.{expected_file_extension}] but the given file name is "{filename}".')
         exit(1)

    if metadata_is_remote:
        app_settings = os.path.join('./', 'app.yaml')
        if os.path.exists(app_settings):
            import yaml
            with open(app_settings) as secrets_file:
                secrets = yaml.load(secrets_file, Loader=yaml.FullLoader)
                for keyword in secrets['env_variables']:
                    os.environ[keyword] = secrets['env_variables'][keyword]
        else:
            print("Error: missing app.yaml file")
            exit(1)

    metadata_validator = PGSMetadataValidator(metadata_filename, metadata_is_remote)
    metadata_validator.parse_spreadsheets()
    metadata_validator.parse_publication()
    metadata_validator.parse_scores()
    metadata_validator.parse_cohorts()
    metadata_validator.parse_performances()
    metadata_validator.parse_samples()
    metadata_validator.post_parsing_checks()

    if metadata_validator.report['error']:
        print("\n#### Reported error(s) ####\n")
        error_report = metadata_validator.report['error']
        for error_spreadsheet in error_report:
            print("# Spreadsheet '"+error_spreadsheet+"'")
            for error_msg in error_report[error_spreadsheet]:
                if error_report[error_spreadsheet][error_msg][0] == None:
                    print('- Global error: '+error_msg)
                else:
                    plural = ''
                    if len(error_report[error_spreadsheet][error_msg]) > 1:
                        plural = 's'
                    print('- Line'+plural+' '+','.join(str(l) for l in error_report[error_spreadsheet][error_msg])+": "+error_msg)

    if metadata_validator.report['warning']:
        print("\n\n#### Reported warning(s) ####")
        warning_report = metadata_validator.report['warning']
        for warning_spreadsheet in warning_report:
            print("\n# Spreadsheet '"+warning_spreadsheet+"'")
            for warning_msg in warning_report[warning_spreadsheet]:
                plural = ''
                if warning_report[warning_spreadsheet][warning_msg][0] == None:
                    print('- Global warning: '+warning_msg)
                else:
                    plural = ''
                    if len(warning_report[warning_spreadsheet][warning_msg]) > 1:
                        plural = 's'
                    print('- Line'+plural+' '+','.join(str(l) for l in warning_report[warning_spreadsheet][warning_msg])+": "+warning_msg)


if __name__ == '__main__':
    main()
