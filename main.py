from flask import Flask, jsonify, request
from flask_cors import CORS
import io
from validator.main_validator import PGSMetadataValidator

app = Flask(__name__)
app.config["DEBUG"] = True
# File size limit set to 4MB (average is 400-500K)
app.config['MAX_CONTENT_LENGTH'] = 4 * 1000 * 1000

# CORS settings
CORS(app)
cors = CORS(app, resources={r"/": {"origins": "*"}})


def add_report_error(depositon_report: dict, report: dict):
    for spreadsheet in report:
        errors = []
        if spreadsheet not in depositon_report.keys():
            depositon_report[spreadsheet] = []
        for message in report[spreadsheet]:
            formatted_message = ''
            if report[spreadsheet][message][0]:
                formatted_message += "(Lines: {}) ".format(report[spreadsheet][message][0])
            formatted_message += message
            errors.append(formatted_message)
        depositon_report[spreadsheet].extend(errors)


@app.route('/validate_metadata', methods=['POST'])
def validate_metadata():
    file = request.files['file']
    bin_file = io.BytesIO(file.read())
    metadata_validator = PGSMetadataValidator(bin_file, False)
    metadata_validator.parse_spreadsheets()
    metadata_validator.parse_publication()
    metadata_validator.parse_scores()
    metadata_validator.parse_cohorts()
    metadata_validator.parse_performances()
    metadata_validator.parse_samples()
    metadata_validator.post_parsing_checks()

    valid = True
    depositon_report = {}
    if metadata_validator.report['error']:
        valid = False
        error_report = metadata_validator.report['error']
        add_report_error(depositon_report, error_report)

    if metadata_validator.report['warning']:
        warning_report = metadata_validator.report['warning']
        add_report_error(depositon_report, warning_report)

    response = {
        "valid": valid,
        "errorMessages": depositon_report
    }

    return jsonify(response)
