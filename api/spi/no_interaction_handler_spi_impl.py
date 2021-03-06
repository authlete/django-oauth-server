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


from authlete.django.handler.spi.no_interaction_handler_spi import NoInteractionHandlerSpi
from .authorization_request_handler_spi_impl                import AuthorizationRequestHandlerSpiImpl


class NoInteractionHandlerSpiImpl(AuthorizationRequestHandlerSpiImpl, NoInteractionHandlerSpi):
    def __init__(self, request):
        super().__init__(request)


    def isUserAuthenticated(self):
        return (self.getUserSubject() is not None)
