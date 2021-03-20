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


from django.contrib.auth.models                                            import User
from authlete.django.handler.spi.authorization_request_handler_spi_adapter import AuthorizationRequestHandlerSpiAdapter
from authlete.types.standard_claims                                        import StandardClaims


class AuthorizationRequestHandlerSpiImpl(AuthorizationRequestHandlerSpiAdapter):
    def __init__(self, request):
        self._user    = None
        self._tried   = False
        self._request = request


    def getUserClaimValue(self, subject, claimName, languageTag):
        # The user identified by the subject.
        user = self.__getUser(subject)
        if user is None:
            return None

        if claimName == StandardClaims.NAME:
            if user.first_name and user.last_name:
                return '{} {}'.format(user.first_name, user.last_name)
        elif claimName == StandardClaims.GIVEN_NAME:
            if user.first_name:
                return user.first_name
        elif claimName == StandardClaims.FAMILY_NAME:
            if user.last_name:
               return user.last_name
        elif claimName == StandardClaims.EMAIL:
            if user.email:
                return user.email
        else:
            return None

        return None


    def __getUser(self, subject):
        if self._tried == False:
            try:
                self._user = User.objects.get(id=subject)
            except:
                self._user = None

            self._tried = True

        return self._user


    def getUserAuthenticatedAt(self):
        user = self._request.user
        if user.is_authenticated == False:
            return 0

        authenticatedAt = user.last_login
        if authenticatedAt is None:
            return 0

        return int(authenticatedAt.timestamp())


    def getUserSubject(self):
        user = self._request.user
        if user.is_authenticated == False:
            return None

        return user.id
