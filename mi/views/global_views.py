from mi.models import Target
from mi.views.base_view import BaseWinMIView


class GlobalWinsView(BaseWinMIView):

    def value_and_number(self, wins):
        confirmed_value = sum(w["total_expected_export_value"] for w in wins)
        confirmed_number = len(wins)
        return confirmed_value, confirmed_number

    def get(self, request):
        response = self._handle_fin_year(request)
        if response:
            return response
        hvc_confirmed = []
        hvc_unconfirmed = []
        non_hvc_confirmed = []
        non_hvc_unconfirmed = []
        hvc_wins = self._hvc_wins()
        non_hvc_wins = self._non_hvc_wins()
        for win in hvc_wins:
            if self._win_status(win) == "confirmed":
                hvc_confirmed.append(win)
            else:
                hvc_unconfirmed.append(win)
        for win in non_hvc_wins:
            if self._win_status(win) == "confirmed":
                non_hvc_confirmed.append(win)
            else:
                non_hvc_unconfirmed.append(win)

        hvc_confirmed_value,hvc_confirmed_number = self.value_and_number(hvc_confirmed)
        hvc_unconfirmed_value, hvc_unconfirmed_number = self.value_and_number(hvc_unconfirmed)
        non_hvc_confirmed_value, non_hvc_confirmed_number = self.value_and_number(non_hvc_confirmed)
        non_hvc_unconfirmed_value, non_hvc_unconfirmed_number = self.value_and_number(non_hvc_unconfirmed)

        targets = Target.objects.filter(financial_year=self.fin_year)
        total_target = sum(t.target for t in targets)
        
        results = {
            "total_target": total_target,
            "wins": {
                "hvc": {
                    "value": {
                        "confirmed": hvc_confirmed_value,
                        "unconfirmed": hvc_unconfirmed_value,
                        "total": hvc_confirmed_value + hvc_unconfirmed_value,
                    },
                    "number": {
                        "confirmed": hvc_confirmed_number,
                        "unconfirmed": hvc_unconfirmed_number,
                        "total": hvc_confirmed_number + hvc_unconfirmed_number,
                    },
                },
                "non_hvc": {
                    "value": {
                        "confirmed": non_hvc_confirmed_value,
                        "unconfirmed": non_hvc_unconfirmed_value,
                        "total": non_hvc_confirmed_value + non_hvc_unconfirmed_value,
                    },
                    "number": {
                        "confirmed": non_hvc_confirmed_number,
                        "unconfirmed": non_hvc_unconfirmed_number,
                        "total": non_hvc_confirmed_number + non_hvc_unconfirmed_number,
                    },
                },
                "total": {
                    "value": {
                        "confirmed": hvc_confirmed_value + non_hvc_confirmed_value,
                        "unconfirmed": hvc_unconfirmed_value + non_hvc_unconfirmed_value,
                        "total": hvc_confirmed_value + non_hvc_confirmed_value +
                                 hvc_unconfirmed_value + non_hvc_unconfirmed_value,
                    },
                    "number": {
                        "confirmed": hvc_confirmed_number + non_hvc_confirmed_number,
                        "unconfirmed": hvc_unconfirmed_number + non_hvc_unconfirmed_number,
                        "total": hvc_confirmed_number + non_hvc_confirmed_number +
                                 hvc_unconfirmed_number + non_hvc_unconfirmed_number,
                    }
                }
            }
        }
        self._fill_date_ranges()
        return self._success(results)
