import factory
import pytest

from django.core.management import call_command

from mi.factories import SectorTeamFactory, SectorFactory
from io import BytesIO

pytestmark = pytest.mark.django_db


def run_command(s3_stub, csv_content, simulate=False):
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
    call_command('update_sector_sector_team', bucket, object_key, simulate=simulate)


@pytest.mark.parametrize(
    'simulate',
    (
        False, True
    ),
)
def test_happy_path(s3_stubber, caplog,  simulate):
    """Test that the command updates the specified records."""
    sectors = SectorFactory.create_batch(
        3,
        name=factory.Iterator(['sector_1', 'sector_2', 'sector_3']),
    )

    sector_teams = SectorTeamFactory.create_batch(
        3,
        name=factory.Iterator(['sector_1_team', 'sector_2_team', 'sector_3_team']),
    )

    csv_content = f"""id,sector,teams
{sectors[0].pk},"{sectors[0].name}","{sector_teams[0].pk}"
{sectors[1].pk},"{sectors[1].name}","{sector_teams[1].pk}"
{sectors[2].pk},"{sectors[2].name}","{sector_teams[2].pk}"
"""
    run_command(s3_stubber, csv_content, simulate=simulate)

    for index, sector in enumerate(sectors):
        sector.refresh_from_db()
        if simulate:
            assert list(sector.sector_team.all()) == []
        else:
            assert sector_teams[index] in sector.sector_team.all()
    assert 'Finished - succeeded: 3, failed: 0' in caplog.text


def test_multiple_sector_teams(s3_stubber, caplog):
    """Test that multiple sector teams can be assigned to a sector"""
    sector = SectorFactory(name='sector_1')
    sector_teams = SectorTeamFactory.create_batch(
        3,
        name=factory.Iterator(['sector_1_team', 'sector_2_team', 'sector_3_team']),
    )

    csv_content = f"""id,sector,teams
{sector.pk},"{sector.name}","{sector_teams[0].pk},{sector_teams[1].pk},{sector_teams[2].pk}"
"""
    run_command(s3_stubber, csv_content)
    sector.refresh_from_db()

    for sector_team in sector_teams:
        assert sector_team in sector.sector_team.all()
    assert 'Finished - succeeded: 1, failed: 0' in caplog.text


def test_sector_sector_team_relationship_already_exists(s3_stubber, capsys):
    """Test a sector that has the sector team relationship already."""
    sector = SectorFactory(name='sector_1')
    sector_team = SectorTeamFactory(name='sector_team')
    sector.sector_team.add(sector_team)

    csv_content = f"""id,sector,teams
{sector.pk},"{sector.name}","{sector_team.pk}"
"""
    run_command(s3_stubber, csv_content)

    sector.refresh_from_db()
    assert sector_team in sector.sector_team.all()
    out, err = capsys.readouterr()
    assert 'No update required [sector_1]' in out


def test_sector_with_other_sector_team(s3_stubber, caplog):
    """Test that a sector has a relationship with another sector team."""
    sector = SectorFactory(name='sector_1')
    old_sector_team = SectorTeamFactory(name='sector_team')
    sector.sector_team.add(old_sector_team)

    sector_team = SectorTeamFactory(name='new sector_team')

    csv_content = f"""id,sector,teams
{sector.pk},"{sector.name}","{sector_team.pk}"
"""
    run_command(s3_stubber, csv_content)

    sector.refresh_from_db()
    assert sector_team in sector.sector_team.all()
    assert old_sector_team not in sector.sector_team.all()
    assert 'Finished - succeeded: 1, failed: 0' in caplog.text


def test_unknown_sector(s3_stubber, caplog):
    """Test an unknown sector."""
    sector_team = SectorTeamFactory(name='sector_team')

    csv_content = f"""id,sector,teams
30000,"hello","{sector_team.pk}"
"""
    run_command(s3_stubber, csv_content)
    assert 'Finished - succeeded: 0, failed: 1' in caplog.text


def test_unknown_sector_team(s3_stubber, caplog):
    """Test an unknown sector team."""
    sector = SectorFactory(name='sector_1')

    csv_content = f"""id,sector,teams
{sector.pk},"{sector.name}","10000"
"""
    run_command(s3_stubber, csv_content)
    sector.refresh_from_db()
    assert list(sector.sector_team.all()) == []
    assert 'Finished - succeeded: 0, failed: 1' in caplog.text


def test_sector_with_multiple_teams_already(s3_stubber, caplog):
    """Test a sector with multiple teams updates correctly."""
    sector = SectorFactory(name='sector_1')
    sector_team_1 = SectorTeamFactory(name='sector_team')
    sector.sector_team.add(sector_team_1)
    sector_team_2 = SectorTeamFactory(name='new sector_team')
    sector.sector_team.add(sector_team_2)

    csv_content = f"""id,sector,teams
{sector.pk},"{sector.name}","{sector_team_1.pk}"
"""
    run_command(s3_stubber, csv_content)

    sector.refresh_from_db()
    assert sector.sector_team.count() == 1
    assert sector_team_1 in sector.sector_team.all()
    assert sector_team_2 not in sector.sector_team.all()
    assert 'Finished - succeeded: 1, failed: 0' in caplog.text
