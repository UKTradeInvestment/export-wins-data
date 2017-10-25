import warnings
from django.test.runner import DiscoverRunner


class CatchWarningsDiscoverRunner(DiscoverRunner):
    """
    Replacement for Django's DiscoverRunner that fails tests
    if they raise a RuntimeWarning. This is to help debug the
    naive datetime warnings in our tests. To use it set an
    environment variable called TEST_RUNNER to the value of
    'test_helpers.runner.CatchWarningsDiscoverRunner'.
    """

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        warnings.filterwarnings("error", category=RuntimeWarning)
        super().run_tests(test_labels, extra_tests=extra_tests, **kwargs)
