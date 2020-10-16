import requests
from validator.generic import *

class Publication():

    not_null_columns = [
        'doi',
        'journal',
        'firstauthor',
        'authors',
        'title',
        'date_publication'
    ]

    column_format = {
        'doi': 'string',
        'pubmed_id': 'integer'
    }

    def __init__(self, doi, pubmed_id):
        self.doi = doi
        self.pubmed_id = pubmed_id

    #def set_pubmed_id(self, pubmed_id):
    #    self.pubmed_id = pubmed_id

    def populate_from_eupmc(self):
        payload = {'format' : 'json'}
        eupmc_url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'
        try:
            payload['query'] = 'doi:' + self.doi
            result = requests.get(eupmc_url, params=payload)
            result = result.json()
            result= result['resultList']['result'][0]
        except:
            payload['query'] = 'ext_id:' + str(self.pubmed_id)
            result = requests.get(eupmc_url, params=payload)
            result = result.json()
            result = result['resultList']['result'][0]

        if not self.doi:
            self.doi = result['doi']
        if not result['pubType'] == 'preprint':
            if result['pmid']:
                self.pubmed_id = result['pmid']
        self.journal = result['journalTitle']
        self.firstauthor = result['authorString'].split(',')[0]
        self.authors = result['authorString']
        self.title = result['title']
        self.date_publication = result['firstPublicationDate']

    def check_data(self):
        validator = PublicationValidator(self)
        validator.check_not_null()
        validator.check_format()
        return validator.report

class PublicationValidator(GenericValidator):

    def __init__(self, object, type="Publication"):
        super().__init__(object,type)
