from validator.request.connector import Connector, ConnectorException


class EFOTrait():

    def __init__(self, id):
        self.id = id
        self.label = None
        self.is_obsolete: bool = False

    def populate_from_efo(self, connector: Connector):
        try:
            response = connector.get_efo_trait(self.id)
            if 'is_obsolete' in response:
                if isinstance(response['is_obsolete'], bool):
                    self.is_obsolete = response['is_obsolete']
                else:
                    self.is_obsolete = str(response['is_obsolete']).lower() in (1, 'true')
            self.label = response['label']
            return True
        except ConnectorException as e:
            connector.logger.debug(e, __name__)
            return False
