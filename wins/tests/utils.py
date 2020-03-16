import json

import mohawk


class HawkMockJSONResponse:
    """
    Mock utility mocking server validation for POST content.
    This is needed when mocking responses when using the APIClient and HawkAuth.

    The default reponse is an empty JSON but can be overridden by passing in a
    response argument into the constructor.

    dynamic_reponse = HawkMockJSONResponse(
        api_id='some-id',
        api_key='some-key'
        response={'content': 'Hello'}
    )

    requests_mock.post(
        'some/api/',
        status_code=status.HTTP_200_OK,
        json=dynamic_reponse,
    )
    """

    def __init__(
        self,
        api_id,
        api_key,
        algorithm='sha256',
        content_type='application/json',
        response=None,
    ):
        """
        Initialise with a dict that can be serialized to json
        this reponse body will be validated and returned in the mock reponse.
        """
        self.credentials = {
            'id': api_id,
            'key': api_key,
            'algorithm': algorithm,
        }
        self._response = response
        self.content_type = content_type
        if self._response is None:
            self._response = {}

    def __call__(self, request, context):
        """
        Mock the server authorization response for validating the response content
        """
        response = json.dumps(self._response)
        credentials = (lambda key: self.credentials)
        receiver = mohawk.Receiver(
            credentials,
            request.headers['Authorization'],
            request.url,
            request.method,
            content=request.text,
            content_type=request.headers['Content-Type'],
        )
        receiver.respond(
            content=response,
            content_type=self.content_type,
        )
        context.headers['Server-Authorization'] = receiver.response_header
        context.headers['Content-Type'] = self.content_type
        return response
