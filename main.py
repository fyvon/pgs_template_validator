#!flask/bin/python
import os
from flask import Flask, request, abort, jsonify
from flask_cors import CORS
from validator.main_validator import PGSMetadataValidator

app = Flask(__name__, static_url_path='/')

# CORS settings
CORS(app)
cors = CORS(app, resources={r"/": {"origins": "*"}})

if not os.getenv('GAE_APPLICATION', None):
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


@app.route("/robots.txt")
def robots_dot_txt():
    return "User-agent: *\nDisallow: /"


@app.route('/', methods=['GET'])
def home():
    return "<h1>Distant Reading Archive</h1><p>This site is a prototype API for distant reading of science fiction novels.</p>"


@app.route('/validate', methods=['POST'])
def post_file():

    response = {}
    post_json = request.get_json()
    #print("post_json: "+str(post_json))

    filename = post_json['filename']

    # Check file extension
    expected_file_extension = 'xlsx'
    filename_only = os.path.basename(filename)
    extension = filename_only.split('.')[-1]
    if extension != expected_file_extension:
        error_msg = { 'message': f'The expected file extension is [.{expected_file_extension}] but the given file name is "{filename_only}".'}
        response = {'status': 'failed', 'error': {} }
        response['error']['General'] = [ error_msg ]
        return jsonify(response)

    url_root = os.environ['STORAGE_ROOT_URL']

    url = f'{url_root}{filename}'
    metadata_validator = PGSMetadataValidator(url, 1)
    loaded_spreadsheets = metadata_validator.parse_spreadsheets()
    if loaded_spreadsheets:
        metadata_validator.parse_publication()
        metadata_validator.parse_scores()
        if metadata_validator.parsed_scores:
            metadata_validator.parse_cohorts()
            metadata_validator.parse_performances()
            metadata_validator.parse_samples()

    status = 'success'
    if metadata_validator.report['error']:
        status = 'failed'
        response['error'] = {}
        error_report = metadata_validator.report['error']
        for error_spreadsheet in error_report:
            response['error'][error_spreadsheet] = []
            for error_msg in error_report[error_spreadsheet]:
                error_entry = { 'message': error_msg }
                if error_report[error_spreadsheet][error_msg][0] != None:
                    error_entry['lines'] = error_report[error_spreadsheet][error_msg]
                response['error'][error_spreadsheet].append(error_entry)

    if metadata_validator.report['warning']:
        response['warning'] = {}
        warning_report = metadata_validator.report['warning']
        for warning_spreadsheet in warning_report:
            response['warning'][warning_spreadsheet] = []
            for warning_msg in warning_report[warning_spreadsheet]:
                warning_entry = { 'message': warning_msg }
                if warning_report[warning_spreadsheet][warning_msg][0] != None:
                    warning_entry['lines'] = warning_report[warning_spreadsheet][warning_msg]
                response['warning'][warning_spreadsheet].append(warning_entry)

    response['status'] = status
    #os.remove(metadata_filename)

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=False)#, port=5000)
    #app.run(debug=True, port=5000)
