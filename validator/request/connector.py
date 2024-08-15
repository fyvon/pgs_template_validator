from abc import abstractmethod, ABC
import importlib
from validator.request.config import URLS
import logging


class ConnectorException(Exception):
    def __init__(self, message=None, url=None):
        super().__init__(message)
        self.url = url


class NotFound(ConnectorException):
    """The requested entity was not found."""
    pass


class ServiceNotWorking(ConnectorException):
    """The requested web service returns a 5xx error code."""
    pass


class UnknownError(ConnectorException):
    """The request returned an unknown error. For example the response might be valid but the content format is not as expected."""
    pass


class Logger(ABC):
    """Logger abstract class for logging any message related to the Connector."""
    def debug(self, message, name=None):
        pass

    def error(self, message, name=None):
        pass

    def info(self, message, name=None):
        pass


class DefaultLogger(Logger):
    """Default implementation of Logger using the 'logging' Python library."""

    def debug(self, message, name=None):
        logging.getLogger(name).debug(message)

    def error(self, message, name=None):
        logging.getLogger(name).error(message)

    def info(self, message, name=None):
        logging.getLogger(name).info(message)


class Connector(ABC):
    """This class handles connections to external web resources and validate the returned responses.
    It is abstract, the method "request" must be implemented in subclasses depending on the environment."""
    def __init__(self, urls: dict = None, logger: Logger = DefaultLogger()):
        self.urls = URLS
        self.logger = logger
        if urls:
            self.urls = self.urls.update(urls)

    @abstractmethod
    def request(self, url, params=None) -> dict:
        """Method performing the HTTP GET request to the given URL. Returns the JSON response as a dictionary."""
        raise NotImplementedError

    def get_publication(self, doi=None, pmid=None) -> dict:
        params = {'format': 'json'}
        if doi:
            params['query'] = 'doi:' + doi
        elif pmid:
            params['query'] = 'ext_id:' + str(pmid)
        else:
            return {}
        response = self.request(self.urls["europepmc"], params)
        # EuropePMC request doesn't return 404 if no result but a valid JSON with an empty 'result' list.
        if 'resultList' in response and 'result' in response['resultList'] and len(response['resultList']['result']) == 1:
            return response['resultList']['result'][0]
        else:
            if doi and pmid:
                try:
                    # Try again with PMID only
                    return self.get_publication(doi=None, pmid=pmid)
                except NotFound:
                    # Then it's definitely not found
                    raise NotFound(message="No result found for DOI:{} or PMID:{}".format(doi, pmid))
            elif doi:
                raise NotFound(message="No result found for DOI:{}".format(doi))
            elif pmid:
                raise NotFound(message="No result found for PMID:{}".format(pmid))

    def get_efo_trait(self, efo_id) -> dict:
        url = self.urls["ols_efo"] + '?obo_id=%s' % efo_id.replace('_', ':')
        response = self.request(url)
        # If not found the response should return 404.
        if '_embedded' in response and 'terms' in response['_embedded'] and len(response['_embedded']['terms']) == 1:
            return response['_embedded']['terms'][0]
        else:
            raise UnknownError(message="Unexpected response from URL: %s" % url, url=url)

    def get_gwas(self, gcst_id) -> dict:
        # Returns 404 if not found.
        return self.request(f'{self.urls["gwas"]}/{gcst_id}')


class DefaultConnector(Connector):
    """Default implementation of Connector using the standard requests python library."""

    def __init__(self):
        super().__init__()
        try:
            self.requests = importlib.import_module('requests')
        except ImportError as e:
            print('"requests" module is missing.')
            raise e

    def __do_request(self, url, params=None) -> dict:
        r = self.requests.get(url, params=params)
        if r.status_code == 404:
            raise NotFound('Status code: %d (%s)' % (r.status_code, url), url)
        if 500 <= r.status_code < 600:
            raise ServiceNotWorking('Status code: %d (%s)' % (r.status_code, url), url)
        if r.status_code != 200:
            raise UnknownError('Status code: %d (%s)' % (r.status_code, url), url)
        return r.json()

    def request(self, url, params=None) -> dict:
        try:
            return self.__do_request(url, params)
        except ConnectorException as e:
            self.logger.debug("Exception: {}. URL: {}".format(str(e), e.url), __name__)
            raise e

