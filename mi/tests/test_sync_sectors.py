from unittest import mock
from datetime import datetime

import pytest
from freezegun import freeze_time

from mi.sync_sectors import SyncSectors
from mi.models import Sector

pytestmark = pytest.mark.django_db

EXISTING_SECTOR = ('133', 'Energy')
EXISTING_SECTOR_2 = ('134', 'Environment')
EXISTING_SECTOR_WITH_ALT_NAME = ('133', 'Renewable energy')
NEW_SECTOR = ('1000', 'Pie makers')


@pytest.mark.parametrize(
    'disable_on,',
    (
        True,  None,
    ),
)
@mock.patch('mi.sync_sectors.SyncSectors.disable_sectors')
@mock.patch('mi.sync_sectors.SyncSectors.update_existing_sectors')
@mock.patch('mi.sync_sectors.SyncSectors.add_new_sectors')
def test_process(mock_add_new, mock_update, mock_disable, disable_on):
    mock_add_new.return_value = None
    mock_update.return_value = None
    mock_disable.return_value = None
    disable_is_called = False
    if disable_on:
        disable_on = datetime.today()
        disable_is_called = True
    sync_sectors = SyncSectors(
        Sector, {}, disable_on=disable_on
    )
    sync_sectors()
    assert mock_add_new.called is True
    assert mock_update.called is True
    assert mock_disable.called is disable_is_called


@pytest.mark.parametrize(
    'sectors,expected_log,simulate',
    (
        (
            [NEW_SECTOR], 'Creating Sector 1000:  [Pie makers]', False,
        ),
        (
            [NEW_SECTOR], 'Creating Sector 1000:  [Pie makers]', True
        ),
        (
            [EXISTING_SECTOR], '', False,
        ),
    ),
)
def test_add_new_sectors(sectors, expected_log, simulate, caplog):
    sync_sectors = SyncSectors(
        Sector, sectors, simulate=simulate,
    )
    sync_sectors.add_new_sectors()
    exists = not simulate
    assert_sectors(sectors, exists)
    assert expected_log in caplog.text


@pytest.mark.parametrize(
    'sectors,expected_log,simulate',
    (
        (
            [EXISTING_SECTOR_WITH_ALT_NAME], 'Updating Sector 133: [Energy to Renewable energy]', False,
        ),
        (
            [EXISTING_SECTOR_WITH_ALT_NAME], 'Updating Sector 133: [Energy to Renewable energy]', True
        ),
    ),
)
def test_update_existing_sector(sectors, expected_log, simulate, caplog):
    assert_sectors(sectors, True, ignore_name=True)
    sync_sectors = SyncSectors(
        Sector, sectors, simulate=simulate,
    )
    sync_sectors.update_existing_sectors()
    exists = not simulate
    assert_sectors(sectors, exists)
    assert expected_log in caplog.text


@pytest.mark.parametrize(
    'sectors,expected_log,simulate',
    (
        (
            [EXISTING_SECTOR], 'Disabling Sector 133: [Energy]', False,
        ),
        (
            [EXISTING_SECTOR], 'Disabling Sector 133: [Energy]', True
        ),
    ),
)
@freeze_time('2020-01-01 12:00:00')
def test_disable_sectors(sectors, expected_log, simulate, caplog):
    assert_sectors(sectors, True)
    sync_sectors = SyncSectors(
        Sector, sectors, simulate=simulate, disable_on=datetime.now()
    )
    sync_sectors.disable_sectors()
    assert expected_log not in caplog.text
    assert_sectors(sectors, True, extra_filters={'disabled_on__isnull': True})
    if not simulate:
        assert_sectors(
            [EXISTING_SECTOR_2], True, extra_filters={'disabled_on': datetime.now()}
        )
    else:
        assert_sectors(
            [EXISTING_SECTOR_2], True, extra_filters={'disabled_on__isnull': True}
        )


def assert_sectors(sectors, exists, extra_filters=None, ignore_name=False):
    sectors = dict(sectors)
    for sector_id, sector_name in sectors.items():
        filters = {'id': sector_id}
        if not ignore_name:
            filters['name'] = sector_name
        if extra_filters:
            filters.update(**extra_filters)
        assert Sector.objects.filter(**filters).exists() == exists
