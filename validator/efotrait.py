import requests

class EFOTrait():

    def __init__(self, id):
        self.id = id
        self.label = None

    def populate_from_efo(self):
        response = requests.get('https://www.ebi.ac.uk/ols/api/ontologies/efo/terms?obo_id=%s'%self.id.replace('_', ':'))
        response = response.json()['_embedded']['terms']
        if len(response) == 1:
            response = response[0]
            self.label = response['label']
            return True
        else:
            return False
