#
# Copyright (C) 2019-2021 Authlete, Inc.
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


import logging
import time
from django.contrib.auth        import logout
from django.contrib.auth.models import User
from django.shortcuts           import render
from authlete.django.handler.authorization_request_base_handler  import AuthorizationRequestBaseHandler
from authlete.django.handler.authorization_request_error_handler import AuthorizationRequestErrorHandler
from authlete.django.handler.no_interaction_handler              import NoInteractionHandler
from authlete.django.web.request_utility                         import RequestUtility
from authlete.dto.authorization_action                           import AuthorizationAction
from authlete.dto.authorization_fail_action                      import AuthorizationFailAction
from authlete.dto.authorization_fail_reason                      import AuthorizationFailReason
from authlete.dto.authorization_fail_request                     import AuthorizationFailRequest
from authlete.dto.authorization_request                          import AuthorizationRequest
from authlete.types.prompt                                       import Prompt
from .authorization_page_model                                   import AuthorizationPageModel
from .base_endpoint                                              import BaseEndpoint
from .spi.no_interaction_handler_spi_impl                        import NoInteractionHandlerSpiImpl


logger = logging.getLogger(__name__)


class AuthorizationEndpoint(BaseEndpoint):
    def __init__(self, api):
        super().__init__(api)


    def handle(self, request):
        # Query parameters or form parameters. OIDC Core 1.0 requires that
        # the authorization endpoint support both GET and POST methods.
        params = RequestUtility.extractParameters(request)

        # Call Authlete's /api/auth/authorization API.
        res = self.__callAuthorizationApi(params)

        # 'action' in the response denotes the next action which this
        # authorization endpoint implementation should take.
        action = res.action

        if action == AuthorizationAction.INTERACTION:
            # Process the authorization request with user interaction.
            return self.__handleInteraction(request, res)
        elif action == AuthorizationAction.NO_INTERACTION:
            # Process the authorization request without user interaction.
            # The flow reaches here only when the authorization request
            # contains 'prompt=none'.
            return self.__handleNoInteraction(request, res)
        else:
            # Handle other error cases.
            return self.__handleError(res)


    def __callAuthorizationApi(self, parameters):
        # Create a request for /api/auth/authorization API.
        req = AuthorizationRequest()
        req.parameters = parameters

        # Call /api/auth/authorization API.
        return self.api.authorization(req)


    def __handleNoInteraction(self, request, response):
        logger.debug("authorization_endpoint: Processing the request without user interaction.")

        # Make NoInteractionHandler handle the case of 'prompt=none'.
        # An implementation of the NoInteractionHandlerSpi interface
        # needs to be given to the constructor of NoInteractionHandler.
        return NoInteractionHandler(
            self.api, NoInteractionHandlerSpiImpl(request)).handle(response)


    def __handleError(self, response):
        logger.debug("authorization_endpoint: The request caused an error: {}".format(response.resultMessage))

        # Make AuthorizationRequestErrorHandler handle the error case.
        return AuthorizationRequestErrorHandler().handle(response)


    def __handleInteraction(self, request, response):
        logger.debug("authorization_endpoint: Processing the request with user interaction.")

        # Prepare a model object which is needed to render the authorization page.
        model = self.__prepareModel(request, response)

        # In the current implementation, model is None only when there is no user
        # who has the required subject.
        if model is None:
            return self.__authorizationFail(
                response.ticket, AuthorizationFailReason.NOT_AUTHENTICATED)

        # Store some variables into the session so that they can be
        # referred to later in authorization_decision_endpoint.py.
        session = request.session
        session['ticket']       = response.ticket
        session['claimNames']   = response.claims
        session['claimLocales'] = response.claimsLocales

        # Render the authorization page.
        return render(request, 'api/authorization.html', {'model':model})


    def __prepareModel(self, request, response):
        # Model object used to render the authorization page.
        model = AuthorizationPageModel(response)

        # Check if login is required.
        model.loginRequired = self.__isLoginRequired(request, response)

        if model.loginRequired == False:
            # The user's name that will be referred to in the authorization page.
            model.userName = request.user.first_name
            return model

        # Logout the user (if a user has logged in).
        logout(request)

        # If the authorization request does not require a specific 'subject'.
        if response.subject is None:
            # This simple implementation uses 'login_hint' as the initial
            # value of the login ID.
            if response.loginHint is not None:
                model.loginId = response.loginHint
            return model

        # The authorization request requires a specific 'subject' be used.

        try:
            # Find the user whose subject is the required subject.
            user = User.objects.get(id=response.subject)
        except:
            # There is no user who has the required subject.
            logger.debug("authorization_endpoint: The request fails because there is no user who has the required subject.")
            return None

        # The user who is identified by the subject exists.
        model.loginId         = user.username
        model.loginIdReadOnly = 'readonly'

        return model


    def __isLoginRequired(self, request, response):
        # If no user has logged in.
        if request.user.is_authenticated == False:
            return True

        # Check if the 'prompt' parameter includes 'login'.
        included = self.__isLoginIncludedInPrompt(response)
        if included:
            # Login is explicitly required by the client.
            # The user has to re-login.
            logger.debug("authorization_endpoint: Login is required because 'prompt' includes 'login'.")
            return True

        # If the authorization request requires a subject.
        if response.subject is not None:
            # If the current user's subject does not match the required one.
            if request.user.id != response.subject:
                # The user needs to login with another user account.
                logger.debug("authorization_endpoint: Login is required because the current user's subject does not match the required one.")
                return True

        # Check if the max age has passed since the last time the user logged in.
        exceeded = self.__isMaxAgeExceeded(request, response)
        if exceeded:
            # The user has to re-login.
            logger.debug("authorization_endpoint: Login is required because the max age has passed since the last login.")
            return True

        # Login is not required.
        return False


    def __isLoginIncludedInPrompt(self, response):
        # If the authorization request does not include a 'prompt' parameter.
        if response.prompts is None:
            return False

        # For each value in the 'prompt' parameter.
        for prompt in response.prompts:
            if prompt == Prompt.LOGIN:
                # 'login' is included in the 'prompt' parameter.
                return True

        # The 'prompt' parameter does not include 'login'.
        return False


    def __isMaxAgeExceeded(self, request, response):
        # If the authorization request does not include a 'max_age' parameter
        # and the 'default_max_age' metadata of the client is not set.
        if response.maxAge <= 0:
            # Don't have to care about the maximum authentication age.
            return False

        # Calculate the number of seconds that have elapsed since the last login.
        age = int(time.time() - request.user.last_login)

        if age <= response.maxAge:
            # The max age is not exceeded yet.
            return False

        # The max age has been exceeded.
        return True


    def __authorizationFail(self, ticket, reason):
        # Call /api/auth/authorization/fail API.
        handler = AuthorizationRequestBaseHandler(self.api)
        return handler.authorizationFail(ticket, reason)
