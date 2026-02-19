from accounts.models import Account


class AccountDashboardService:
    @staticmethod
    def sidebar_groups_for_profile(*, profile):
        accounts = (
            Account.objects.filter(portfolio__profile=profile)
            .select_related("account_type")
            .prefetch_related("holdings")
            .order_by("account_type__name", "name")
        )

        groups: dict[str, dict] = {}
        for account in accounts:
            type_name = account.account_type.name
            entry = groups.setdefault(
                type_name,
                {
                    "group_key": account.account_type.slug or type_name.lower().replace(" ", "_"),
                    "group_label": type_name,
                    "accounts": [],
                },
            )
            entry["accounts"].append(
                {
                    "id": account.id,
                    "name": account.name,
                    "broker": account.broker,
                    "holdings_count": account.holdings.count(),
                    "last_synced": account.last_synced,
                }
            )

        return list(groups.values())

