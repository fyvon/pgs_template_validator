# PGS Catalog template validator

Standalone Python validator for the **PGS Catalog Curation Template** (Metadata)

For more information about the PGS Catalog submission and its template, go to this page: [https://www.pgscatalog.org/submit/](https://www.pgscatalog.org/submit/)

## Example of command

### As command line
```
python pgs_metadata_validator.py -f <my_template_file>.xlsx
```

### As REST API endpoint
To launch the REST API (Flask)
```
python main.py
```

and then send the request to validate the file, e.g. with **curl**:
```
curl -X POST -H "Content-Type: application/json" -d "{ \"filename\": \"<my_template_file>.xlsx\" }" http://127.0.0.1:5000/validate
```

## Deploy it as a REST API service on Google Cloud (App Engine)

Only possible if you already have a Google Cloud account!

To deploy it:
* Rename __app.yaml_template__ to __app.yaml__
* Update __app.yaml__ by replacing the variable(s) between __<>__ with the right value(s)
* Install the (Cloud SDK)[https://cloud.google.com/sdk] if you don't have it
* Run `gcloud app deploy` in this repository
