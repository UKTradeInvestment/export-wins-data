from random import randint

from mi.models import UKRegionTarget


class TestUKRegionTarget:

    def test_as_dict(self):
        uk_region_target = UKRegionTarget(
            new_exporters=_generate_monthly_targets(),
            sustainable=_generate_monthly_targets(),
            growth=_generate_monthly_targets(),
            unknown=_generate_monthly_targets(),
        )

        new_exporters_total = sum(uk_region_target.new_exporters)
        sustainable_total = sum(uk_region_target.sustainable)
        growth_total = sum(uk_region_target.growth)
        unknown_total = sum(uk_region_target.unknown)

        assert uk_region_target.as_dict() == {
            'target': {
                'new_exporters': new_exporters_total,
                'sustainable': sustainable_total,
                'growth': growth_total,
                'unknown': unknown_total,
                'total': new_exporters_total + sustainable_total + growth_total + unknown_total,
                'type': 'volume'
            },
        }


def _generate_monthly_targets():
    return [randint(0, 100) for _ in range(12)]
