import os, sys, glob, re
import argparse
from validator.main_validator import PGSMetadataValidator

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-f", help='The path to the PGS Catalog metadata file to be validated', metavar='PGS_METADATA_FILE_NAME')
    #argparser.add_argument('--log_dir', help='The name of the log directory where the log file(s) will be stored', required=True)

    args = argparser.parse_args()

    # Check study file exists
    metadata_filename = args.f
    if not os.path.isfile(metadata_filename):
        print("File '"+metadata_filename+"' can't be found")
        exit(1)


    metadata_validator = PGSMetadataValidator(metadata_filename)
    metadata_validator.parse_spreadsheets()
    metadata_validator.parse_publication()
    metadata_validator.parse_scores()
    metadata_validator.parse_performances()
    metadata_validator.parse_samples()

    if metadata_validator.report['error']:
        print("\n#### Reported error(s) ####\n")
        for error_spreadsheet in metadata_validator.report['error']:
            print("# Spreadsheet '"+error_spreadsheet+"'")
            print('- '+'\n- '.join(metadata_validator.report['error'][error_spreadsheet]))
    if metadata_validator.report['warning']:
        print("\n\n#### Reported warning(s) ####\n")
        for error_spreadsheet in metadata_validator.report['warning']:
            print("# Spreadsheet '"+error_spreadsheet+"'")
            print('- '+'\n- '.join(metadata_validator.report['warning'][error_spreadsheet]))


if __name__ == '__main__':
    main()
