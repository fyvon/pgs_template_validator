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


def format_report_error(report: dict) -> list:
    errors = []
    for spreadsheet in report:
        for message in report[spreadsheet]:
            formatted_message = spreadsheet
            if report[spreadsheet][message][0]:
                formatted_message += " (lines: {})".format(report[spreadsheet][message][0])
            formatted_message += ": " + message
            errors.append(formatted_message)
    return errors


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
    errors = []
    if metadata_validator.report['error']:
        valid = False
        error_report = metadata_validator.report['error']
        errors.extend(format_report_error(error_report))

    if metadata_validator.report['warning']:
        warning_report = metadata_validator.report['warning']
        errors.extend(format_report_error(warning_report))

    response = {
        "valid": valid,
        "errors": errors
    }

    return jsonify(response)
