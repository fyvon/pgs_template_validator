import requests

class EFOTrait():

    def __init__(self, id):
        self.id = id
        self.label = None

    def populate_from_efo(self):
        response = requests.get('https://www.ebi.ac.uk/ols/api/ontologies/efo/terms?obo_id=%s'%self.id.replace('_', ':'))
        if response.status_code == 200:
            response = response.json()['_embedded']['terms']
            if len(response) == 1:
                response = response[0]
                self.label = response['label']
                return True
        return False