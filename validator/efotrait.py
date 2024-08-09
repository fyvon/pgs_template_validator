from validator.request.connector import Connector, ConnectorException


class EFOTrait():

    def __init__(self, id):
        self.id = id
        self.label = None

    def populate_from_efo(self, connector: Connector):
        try:
            response = connector.get_efo_trait(self.id)
            self.label = response['label']
            return True
        except ConnectorException as e:
            return False
