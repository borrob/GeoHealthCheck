import sys
import requests
from factory import Factory
from result import ProbeResult, CheckResult

class Probe(object):
    """
     Base class for specific Request&Check implementations.

    """

    # Generic attributes, subclassses override
    AUTHOR = 'GHC Team'
    NAME = 'Fill in Name'
    DESCRIPTION = 'Fill in Description'
    RESOURCE_TYPE = '*'

    # Request attributes
    REQUEST_METHOD = 'GET'
    REQUEST_HEADERS = None
    REQUEST_TEMPLATE = ''
    REQUEST_PARAMETERS = None

    # Possible response checks attributes
    RESPONSE_CHECKS = None

    # Lifecycle
    def init(self, config=None):
        # Config contains the actual parameters (from Models/DB) for Request and Checks
        self.config = config
        self.response = None
        self.result = None

    # Lifecycle
    def exit(self):
        pass

    def log(self, text):
        print('%s: %s' % (self.__class__.__name__, text))

    def create_result(self):
        """ Create ProbeResult object that gathers all results for single Probe"""

        self.result = ProbeResult(self)

    def create_check_result(self, check, parameters, success, message):
        """ Create CheckResult object that gathers all results for single Check"""

        return CheckResult(check, parameters, success, message)

    def before_request(self):
        """ Before running actual request to service"""

        self.create_result()

        self.result.start()

    def after_request(self):
        """ After running actual request to service"""

        self.result.stop()

    def perform_request(self):
        """ Perform actual request to service"""

        # Actualize request query string or POST body
        # by substitution in template.
        url_base = self.config.resource.url

        request_string = None
        if self.REQUEST_TEMPLATE:
            request_parms = self.config.parameters
            request_string = self.REQUEST_TEMPLATE.format(**request_parms)

        self.log('Doing request: method=%s url=%s' % (self.REQUEST_METHOD, url_base))

        if self.REQUEST_METHOD == 'GET':
            # Default is plain URL, e.g. for WWW:LINK
            url = url_base
            if request_string:
                # Query String: mainly OWS:* resources
                url = "%s?%s" % (url, request_string)
                
            self.response = requests.get(url,
                                         headers=self.REQUEST_HEADERS)
        elif self.REQUEST_METHOD == 'POST':
            self.response = requests.post(url_base,
                                          data=request_string,
                                          headers=self.REQUEST_HEADERS)

        self.log('response: status=%d' % (self.response.status_code))
        if self.response.status_code /100 in [4,5]:
            self.log('Errro response: %s' % (str(self.response.text)))


    def run_request(self):
        """ Run actual request to service"""
        self.before_request()
        self.perform_request()
        self.after_request()

    def run_checks(self):
        """ Do the checks on the response from request"""

        # Config also determines which actual checks are performed from possible
        # Checks in Probe
        checks = self.config.checks
        for check in checks:
            fun_str = check.check_identifier
            fun = Factory.create_function(fun_str)
            try:
                result = fun(self, check.parameters)
            except:
                msg = "Exception: %s" % str(sys.exc_info())
                self.log(msg)
                result = False, msg
            self.log('Check: fun=%s result=%s' % (fun_str, result[0]))

            self.result.add_result(self.create_check_result(
                check, check.parameters, result[0], result[1]))
     # Lifecycle
    def calc_result(self):
        """ Calculate overall result from the Result object"""
        self.log("Result: %s" % str(self.result))

    @staticmethod
    def run(config):
        """ Class method to create and run a single Probe"""

        # Create Probe instance from module.class string
        probe = Factory.create_obj(config.request_identifier)

        # Initialize with actual parameters
        probe.init(config)

        # Perform request
        probe.run_request()

        # Perform the Probe's checks
        probe.run_checks()

        # Determine result
        probe.calc_result()

        # Lifecycle
        probe.exit()

        # Return result
        return probe.result

    def __str__(self):
        return "%s" % str(self.__class__)
