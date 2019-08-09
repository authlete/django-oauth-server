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


from django.contrib.auth import authenticate
from authlete.django.handler.spi.token_request_handler_spi_adapter import TokenRequestHandlerSpiAdapter


class TokenRequestHandlerSpiImpl(TokenRequestHandlerSpiAdapter):
    def authenticateUser(self, username, password):
        # NOTE:
        # This method needs to be implemented only when you want to support
        # "Resource Owner Password Credentials" flow (RFC 6749, 4.3.)

        # Authenticate the user with the given credentials.
        user = authenticate(username=username, password=password)

        # If the user is not found.
        if user is None or user.is_active == False:
            # There is no user who has the credentials.
            return None

        # Return the subject (= unique identifier) of the user.
        return user.id
