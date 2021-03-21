#
# Copyright (C) 2021 Authlete, Inc.
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


# This class is an implementation of Django's authentication backends.
# This implementation delegates user authentication to Amazon Cognito.
#
# A Django authentication backend has to implement two methods;
# `authenticate(request, **credentials)` and `get_user(user_id)`.
# This class implements the two methods by using Cognito's
# `AdminInitiateAuth` API and `AdminGetUser` API, respectively.
#
# References:
#
#   Customizing authentication in Django
#     https://docs.djangoproject.com/en/3.1/topics/auth/customizing/
#
#   AWS SDK for Python (Boto3) / CognitoIdentityProvider
#     https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cognito-idp.html
#
#   AdminInitiateAuth API
#     https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_AdminInitiateAuth.html
#
#   AdminGetUser API
#     https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_AdminGetUser.html
#


import boto3
import logging
from django.conf                    import settings
from django.contrib.auth.backends   import BaseBackend
from django.contrib.auth.models     import User
from authlete.types.standard_claims import StandardClaims


logger = logging.getLogger(__name__)


class CognitoBackend(BaseBackend):
    def __init__(self):
        # Create an instance to access Cognito APIs.
        self._cognito_idp = boto3.client('cognito-idp')


    def authenticate(self, request, username=None, password=None):
        # Call Cognito's AdminInitiateAuth API.
        response = self.__cognito_admin_initiate_auth(username, password)
        if response is None:
            # The user was not authenticated.
            return None

        # Build a User object for the authenticated user.
        return self.get_user(username)


    def get_user(self, user_id):
        # Call Cognito's AdminGetUser API.
        response = self.__cognito_admin_get_user(user_id)
        if response is None:
            # Information about the user was not available.
            return None

        # Build a User object based on the information in the response.
        return self.__build_user(user_id, response)


    def __cognito_admin_initiate_auth(self, username, password):
        # If settings for Cognito are not available.
        if not settings.COGNITO_USER_POOL_ID:
            return None

        try:
            # Call Cognito's AdminInitiateAuth API.
            return self.__call_cognito_admin_initiate_auth(username, password)
        except self._cognito_idp.exceptions.NotAuthorizedException:
            # There is no user who has the username and the password.
            logger.debug("Cognito user authentication for '%s' failed.", username)
            return None
        except Exception:
            # Something wrong happened in calling Cognito AdminInitiateAuth API.
            logger.error("Cognito AdminInitiateAuth API failed.", exc_info=True)
            return None


    def __call_cognito_admin_initiate_auth(self, username, password):
        # Call Cognito's AdminInitiateAuth API.
        return self._cognito_idp.admin_initiate_auth(
            UserPoolId     = settings.COGNITO_USER_POOL_ID,
            ClientId       = settings.COGNITO_CLIENT_ID,
            AuthFlow       = 'ADMIN_USER_PASSWORD_AUTH',
            AuthParameters = {
                'USERNAME' : username,
                'PASSWORD' : password
            }
        )


    def __cognito_admin_get_user(self, username):
        # If settings for Cognito are not available.
        if not settings.COGNITO_USER_POOL_ID:
            return None

        try:
            # Call Cognito's AdminGetUser API.
            return self.__call_cognito_admin_get_user(username)
        except self._cognito_idp.exceptions.UserNotFoundException:
            # The user was not found in the Cognito User Pool.
            logger.debug("The user '%s' was not found in the Cognito User Pool.", username)
            return None
        except Exception:
            # Something wrong happened in calling Cognito AdminGetUser API.
            logger.error("Cognito AdminGetUser API failed.", exc_info=True)
            return None


    def __call_cognito_admin_get_user(self, username):
        # Call Cognito's AdminGetUser API.
        return self._cognito_idp.admin_get_user(
            UserPoolId = settings.COGNITO_USER_POOL_ID,
            Username   = username
        )


    def __build_user(self, user_id, response):
        try:
            # Search the list of Django User objects for the user.
            user = User.objects.get(username = user_id)
        except User.DoesNotExist:
            # Create a new Django User object for the user.
            user = User.objects.create_user(user_id)

        # If the response from Cognito's AdminGetUser does not contain
        # 'UserAttributes'
        if 'UserAttributes' not in response:
            return user

        for attribute in response['UserAttributes']:
            name  = attribute['Name']
            value = attribute['Value']

            # Cognito User Pool supports most of standard claims defined in
            # "OpenID Connect Core 1.0 Section 5.1. Standard Claims". However,
            # the default User object of Django does not. If you want to
            # support more claims, you have to customize the User object and
            # then add more 'elif' here and getUserClaimValue() method in
            # AuthorizationRequestHandlerSpiImpl class.
            if name == StandardClaims.EMAIL:
                user.email = value
            elif name == StandardClaims.GIVEN_NAME:
                user.first_name = value
            elif name == StandardClaims.FAMILY_NAME:
                user.last_name = value

        user.save()

        return user
