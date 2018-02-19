from django.urls import reverse
from freezegun import freeze_time

from fdi.tests.base import FdiBaseTestCase


@freeze_time(FdiBaseTestCase.frozen_date_17)
class SectorTeamListTestCase(FdiBaseTestCase):
    """
    Tests covering SectorTeam overview and detail API endpoints
    """

    url = reverse("fdi:sector_teams") + "?year=2017"

    def test_sector_teams_list(self):
        """ test `SectorTeam` list API """

        self.expected_response = sorted([
            {
                "id": 1,
                "name": "Aero",
                "description": "Aerospace"
            },
            {
                "id": 2,
                "name": "AESC",
                "description": "Advanced Engineering and Supply Chains"
            },
            {
                "id": 3,
                "name": "Agri",
                "description": "Agriculture"
            },
            {
                "id": 4,
                "name": "Auto",
                "description": "Automotive"
            },
            {
                "id": 5,
                "name": "BPS",
                "description": "Business and Professional Services"
            },
            {
                "id": 6,
                "name": "Chem",
                "description": "Chemicals"
            },
            {
                "id": 7,
                "name": "Creative",
                "description": "Creative"
            },
            {
                "id": 8,
                "name": "D&S",
                "description": "Defence and Security"
            },
            {
                "id": 9,
                "name": "F&D",
                "description": "Food and Drink"
            },
            {
                "id": 10,
                "name": "FS",
                "description": "Financial Services"
            },
            {
                "id": 11,
                "name": "Infrastructure",
                "description": "Infrastructure"
            },
            {
                "id": 12,
                "name": "Life S",
                "description": "Life Sciences"
            },
            {
                "id": 13,
                "name": "Marine",
                "description": "Marine"
            },
            {
                "id": 14,
                "name": "Nuclear",
                "description": "Nuclear Energy"
            },
            {
                "id": 15,
                "name": "O&G",
                "description": "Oil and Gas"
            },
            {
                "id": 16,
                "name": "Rail",
                "description": "Railways"
            },
            {
                "id": 17,
                "name": "Renew",
                "description": "Renewable Energy"
            },
            {
                "id": 18,
                "name": "Retail",
                "description": "Retail"
            },
            {
                "id": 19,
                "name": "Space",
                "description": "Space"
            },
            {
                "id": 20,
                "name": "Tech",
                "description": "Technology"
            },
            {
                "id": 21,
                "name": "Other",
                "description": "Other"
            }
        ], key=lambda x: (x["id"]))
        self.assertResponse()
