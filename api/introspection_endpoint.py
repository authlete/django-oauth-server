#
# Copyright (C) 2019 Authlete, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific
# language governing permissions and limitations under the
# License.


from authlete.django.handler.introspection_request_handler import IntrospectionRequestHandler
from authlete.django.web.basic_credentials                 import BasicCredentials
from authlete.django.web.response_utility                  import ResponseUtility
from .base_endpoint                                        import BaseEndpoint


class IntrospectionEndpoint(BaseEndpoint):
    def __init__(self, api):
        super().__init__(api)


    def handle(self, request):
        # "1.1. Introspection Request" in RFC 7662 says as follows:
        #
        #   To prevent token scanning attacks, the endpoint MUST also require
        #   some form of authorization to access this endpoint, such as client
        #   authentication as described in OAuth 2.0 [RFC6749] or a separate
        #   OAuth 2.0 access token such as the bearer token described in OAuth
        #   2.0 Bearer Token Usage [RFC6750]. The methods of managing and
        #   validating these authentication credentials are out of scope of
        #   this specification.
        #
        # Therefore, this API must be protected in some way or other. Let's
        # perform authentication of the API caller.
        authenticated = self.__authenticate_api_caller(request)

        # If the API caller does not have necessary privilages to call this API.
        if authenticated == False:
            # 401 Unauthorized
            return ResponseUtility.unauthorized('Basic realm="/api/introspection"')

        # Call Authlete's /api/auth/introspection/standard API.
        return IntrospectionRequestHandler(self.api).handle(request)


    def __authenticate_api_caller(self, request):
        # NOTE: THIS IMPLEMENTATION IS FOR DEMONSTRATION PURPOSES ONLY.

        # Get the value of the Authorization header.
        auth = request.headers.get('Authorization')

        # Try to parse it as "Basic Authentication"
        credentials = BasicCredentials.parse(auth)

        # If the Authorization header does not contain "Basic Authentication"
        # or the user ID is not valid.
        if credentials.userId is None:
            # Authentication of the API caller failed.
            return False

        # If the user ID is "nobody"
        if credentials.userId == 'nobody':
            # Reject the introspection request from "nobody".
            return False

        # Accept anybody except "nobody" regardless of whatever the value of
        # credentials.password is.
        return True
