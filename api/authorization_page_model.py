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


class AuthorizationPageModel(object):
    def __init__(self, response):
        client = response.client

        self._serviceName     = response.service.serviceName
        self._clientName      = client.clientName
        self._description     = client.description
        self._logoUri         = client.logoUri
        self._clientUri       = client.clientUri
        self._policyUri       = client.policyUri
        self._tosUri          = client.tosUri
        self._scopes          = response.scopes
        self._loginId         = ''
        self._loginIdReadOnly = ''
        self._userName        = None


    @property
    def serviceName(self):
        return self._serviceName


    @property
    def clientName(self):
        return self._clientName


    @property
    def description(self):
        return self._description


    @property
    def logoUri(self):
        return self._logoUri


    @property
    def clientUri(self):
        return self._clientUri


    @property
    def policyUri(self):
        return self._policyUri


    @property
    def tosUri(self):
        return self._tosUri


    @property
    def scopes(self):
        return self._scopes


    @property
    def loginId(self):
        return self._loginId


    @loginId.setter
    def loginId(self, value):
        self._loginId = value


    @property
    def loginIdReadOnly(self):
        return self._loginIdReadOnly


    @loginIdReadOnly.setter
    def loginIdReadOnly(self, value):
        self._loginIdReadOnly = value


    @property
    def loginRequired(self):
        return self._loginRequired


    @loginRequired.setter
    def loginRequired(self, value):
        self._loginRequired = value


    @property
    def userName(self):
        return self._userName


    @userName.setter
    def userName(self, value):
        self._userName = value
