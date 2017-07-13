from mi.views.base_view import BaseWinMIView


class GlobalWinsView(BaseWinMIView):
    def get(self, request):
        response = self._handle_fin_year(request)
        if response:
            return response
        hvc_confirmed = []
        hvc_unconfirmed = []
        non_hvc_confirmed = []
        non_hvc_unconfirmed = []
        wins = list(self._wins())
        for win in wins:
            if win['hvc']:
                if self._win_status(win) == 'confirmed':
                    hvc_confirmed.append(win)
                else:
                    hvc_unconfirmed.append(win)
            else:
                if self._win_status(win) == 'confirmed':
                    non_hvc_confirmed.append(win)
                else:
                    non_hvc_unconfirmed.append(win)

        hvc_confirmed_value = sum(w['total_expected_export_value'] for w in hvc_confirmed)
        hvc_confirmed_number = len(hvc_confirmed)
        hvc_unconfirmed_value = sum(w['total_expected_export_value'] for w in hvc_unconfirmed)
        hvc_unconfirmed_number = len(hvc_unconfirmed)

        non_hvc_confirmed_value = sum(w['total_expected_export_value'] for w in non_hvc_confirmed)
        non_hvc_confirmed_number = len(non_hvc_confirmed)
        non_hvc_unconfirmed_value = sum(w['total_expected_export_value'] for w in non_hvc_unconfirmed)
        non_hvc_unconfirmed_number = len(non_hvc_unconfirmed)

        results = {
            'total_target': 0,
            "wins": {
                "hvc": {
                    'value': {
                        'confirmed': hvc_confirmed_value,
                        'unconfirmed': hvc_unconfirmed_value,
                        'total': hvc_confirmed_value + hvc_unconfirmed_value,
                    },
                    'number': {
                        'confirmed': hvc_confirmed_number,
                        'unconfirmed': hvc_unconfirmed_number,
                        'total': hvc_confirmed_number + hvc_unconfirmed_number,
                    },
                },
                "non_hvc": {
                    'value': {
                        'confirmed': non_hvc_confirmed_value,
                        'unconfirmed': non_hvc_unconfirmed_value,
                        'total': non_hvc_confirmed_value + non_hvc_unconfirmed_value,
                    },
                    'number': {
                        'confirmed': non_hvc_confirmed_number,
                        'unconfirmed': non_hvc_unconfirmed_number,
                        'total': non_hvc_confirmed_number + non_hvc_unconfirmed_number,
                    },
                },
                "total": {
                    'value': {
                        'confirmed': hvc_confirmed_value + non_hvc_confirmed_value,
                        'unconfirmed': hvc_unconfirmed_value + non_hvc_unconfirmed_value,
                        'total': hvc_confirmed_value + non_hvc_confirmed_value +
                                 hvc_unconfirmed_value + non_hvc_unconfirmed_value,
                    },
                    'number': {
                        'confirmed': hvc_confirmed_number + non_hvc_confirmed_number,
                        'unconfirmed': hvc_unconfirmed_number + non_hvc_unconfirmed_number,
                        'total': hvc_confirmed_number + non_hvc_confirmed_number +
                                 hvc_unconfirmed_number + non_hvc_unconfirmed_number,
                    }
                }
            }
        }
        self._fill_date_ranges()
        return self._success(results)
