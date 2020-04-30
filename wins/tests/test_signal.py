from unittest.mock import patch

import pytest

from wins.factories import WinFactory


@pytest.fixture
def patch_transaction():
    with patch('django.db.transaction.on_commit') as mock_tansaction:
        yield mock_tansaction


@pytest.mark.django_db
class TestMatchIdSignal:
    """Test post save signal for win model to update match id."""

    def test_signal_on_created_win(self, patch_transaction):
        """Test signal is triggered on create."""
        WinFactory.create(
            id='00000000-0000-0000-0000-000000000000',
            company_name='Name 1',
            cdms_reference='00000000',
            customer_email_address='test@example.com',
        )
        assert patch_transaction.called

    def test_signal_on_updated_win(self, patch_transaction):
        """Test signal is triggered on create and update."""
        win = WinFactory.create(
            id='00000000-0000-0000-0000-000000000000',
            company_name='Name 1',
            cdms_reference='00000000',
            customer_email_address='test@example.com',
        )
        win.company_name = 'Name 2'
        win.save()
        assert patch_transaction.call_count == 2

    def test_ignore_match_id_post_save(self, patch_transaction):
        """Test signal does not run task if the match id has been updated with update_fields."""
        win = WinFactory.create(
            id='00000000-0000-0000-0000-000000000000',
            company_name='Name 1',
            cdms_reference='00000000',
            customer_email_address='test@example.com',
            match_id=1
        )

        win.match_id = 2
        win.save(update_fields=['match_id'])

        assert patch_transaction.call_count == 1
