from io import BytesIO
from uuid import UUID

import factory
import pytest
from django.core.management import call_command

from mi.factories import SectorFactory
from wins.factories import WinFactory
from wins.models import Win


@pytest.fixture
def create_wins_in_db():
    sectors = SectorFactory.create_batch(
        3,
        id=factory.Iterator([10001, 10002, 10003]),
        name=factory.Iterator(['sector_1', 'sector_2', 'sector_3']),
    )
    WinFactory.create(
        id='00000000-0000-0000-0000-000000000000',
        company_name='Name 1',
        cdms_reference='00000000',
        customer_email_address='test@example.com',
        sector=sectors[0].id,
    )
    WinFactory.create(
        id='00000000-0000-0000-0000-000000000001',
        company_name='Name 2',
        cdms_reference='cdms00000000',
        customer_email_address='test@example.com',
        sector=sectors[1].id,
    )
    WinFactory.create(
        id='00000000-0000-0000-0000-000000000002',
        company_name='Name 2',
        cdms_reference='cdms00000000',
        customer_email_address='test@example.com',
        sector=sectors[2].id,
    )


@pytest.mark.django_db
class TestUpdateWinSectorIds:
    """Testing update_win_sector_ids Django management command."""

    @pytest.mark.parametrize(
        'win_csv,expected_win_db_sectors,expected_output,simulate',
        (
            (
                'win_id,old_sector_id,new_sector_id\n'
                '00000000-0000-0000-0000-000000000000,10001,10002\n'
                '00000000-0000-0000-0000-000000000001,10002,10003\n'
                '00000000-0000-0000-0000-000000000003,10003,10003',
                [
                    {'id': UUID('00000000-0000-0000-0000-000000000000'), 'sector': 10002},
                    {'id': UUID('00000000-0000-0000-0000-000000000001'), 'sector': 10003},
                    {'id': UUID('00000000-0000-0000-0000-000000000002'), 'sector': 10003}
                ],
                [
                    'Saved sector 10002 to win 00000000-0000-0000-0000-000000000000',
                    'Saved sector 10003 to win 00000000-0000-0000-0000-000000000001',
                    'No update required for win 00000000-0000-0000-0000-000000000003',
                    'Total records: 3',
                    'Unprocessed: 0',
                    'Updated: 2',
                    'Skipped: 1',
                    'Errors: 0',
                ],
                False,
            ),
            (
                'win_id,old_sector_id,new_sector_id\n'
                '00000000-0000-0000-0000-000000000000,10001,10002\n'
                '00000000-0000-0000-0000-000000000001,10002,10003\n'
                '00000000-0000-0000-0000-000000000003,10003,10003',
                [
                    {'id': UUID('00000000-0000-0000-0000-000000000000'), 'sector': 10001},
                    {'id': UUID('00000000-0000-0000-0000-000000000001'), 'sector': 10002},
                    {'id': UUID('00000000-0000-0000-0000-000000000002'), 'sector': 10003}
                ],
                [
                    'Saved sector 10002 to win 00000000-0000-0000-0000-000000000000',
                    'Saved sector 10003 to win 00000000-0000-0000-0000-000000000001',
                    'No update required for win 00000000-0000-0000-0000-000000000003',
                    'Total records: 3',
                    'Unprocessed: 0',
                    'Updated: 2',
                    'Skipped: 1',
                    'Errors: 0',
                ],
                True,
            ),
            (
                'win_id,old_sector_id,new_sector_id\n'
                '00000000-0000-0000-0000-000000000005,10001,10002\n'
                '00000000-0000-0000-0000-000000000001,10002,10003',
                [
                    {'id': UUID('00000000-0000-0000-0000-000000000000'), 'sector': 10001},
                    {'id': UUID('00000000-0000-0000-0000-000000000001'), 'sector': 10003},
                    {'id': UUID('00000000-0000-0000-0000-000000000002'), 'sector': 10003}
                ],
                [
                    'Skipping due to an invalid ID (00000000-0000-0000-0000-000000000005/10002)',
                    'Saved sector 10003 to win 00000000-0000-0000-0000-000000000001',
                    'Total records: 3',
                    'Unprocessed: 2',
                    'Updated: 1',
                    'Skipped: 0',
                    'Errors: 1',
                ],
                False,
            ),
            (
                'win_id,old_sector_id,new_sector_id\n'
                '00000000-0000-0000-0000-000000000000,10001,600',
                [
                    {'id': UUID('00000000-0000-0000-0000-000000000000'), 'sector': 10001},
                    {'id': UUID('00000000-0000-0000-0000-000000000001'), 'sector': 10002},
                    {'id': UUID('00000000-0000-0000-0000-000000000002'), 'sector': 10003}
                ],
                [
                    'Skipping due to an invalid ID (00000000-0000-0000-0000-000000000000/600)',
                    'Total records: 3',
                    'Unprocessed: 3',
                    'Updated: 0',
                    'Skipped: 0',
                    'Errors: 1',
                ],
                False,
            )
        ),
    )
    def test_win_sector_update(
            self,
            simulate,
            expected_output,
            expected_win_db_sectors,
            win_csv,
            s3_stubber,
            capsys,
            create_wins_in_db,
    ):
        """Test the update_win_sector_ids command to give expected output"""
        self.run_command(s3_stubber, win_csv, simulate)
        assert list(Win.objects.values('id', 'sector').order_by('id')) == expected_win_db_sectors
        out, err = capsys.readouterr()
        for line in expected_output:
            assert line in out

    def run_command(self, s3_stub, csv_content, simulate=False):
        bucket = 'test_bucket'
        object_key = 'test_key'
        s3_stub.add_response(
            'get_object',
            {
                'Body': BytesIO(csv_content.encode(encoding='utf-8')),
            },
            expected_params={
                'Bucket': bucket,
                'Key': object_key,
            },
        )
        call_command('update_win_sector_ids', bucket, object_key, simulate=simulate)
