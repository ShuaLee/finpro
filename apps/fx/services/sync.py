from external_data.fmp.fx.fetchers import fetch_fx_universe, fetch_fx_quotes_bulk, fetch_fx_quote
from fx.models.fx import FXCurrency, FXRate


class FXSyncService:

    @classmethod
    def sync_currencies(cls):
        """
        Pull currency list from forex-list and update FXCurrency table.
        """
        data = fetch_fx_universe()

        if not data:
            return 0

        created = 0

        for row in data:
            for code, name in [
                (row["fromCurrency"], row.get("fromName")),
                (row["toCurrency"], row.get("toName")),
            ]:
                code = code.upper()

                obj, was_created = FXCurrency.objects.update_or_create(
                    code=code,
                    defaults={"name": name},
                )
                if was_created:
                    created += 1

        return created

    # ============================================================
    # 2) SYNC A **SINGLE PAIR**
    # ============================================================
    @classmethod
    def sync_single_pair(cls, base: str, quote: str):
        """
        Sync a single FX pair BASE->Quote
        """
        data = fetch_fx_quote(base, quote)
        if not data:
            return False

        base_code = data["from"].upper()
        quote_code = data["to"].upper()

        base_cur, _ = FXCurrency.objects.get_or_create(code=base_code)
        quote_cur, _ = FXCurrency.objects.get_or_create(code=quote_code)

        FXRate.objects.update_or_create(
            from_currency=base_cur,
            to_currency=quote_cur,
            defaults={"rate": data["rate"]}
        )

        return True

    @classmethod
    def sync_rates_for_symbols(cls, symbols: list[str]):
        """
        Refresh FXRate entries for given forex symbols (e.g. ["USDJPY", "EURCAD"]).
        """
        if not symbols:
            return 0

        results = fetch_fx_quotes_bulk(symbols)
        updated = 0

        for r in results:
            base = r["from"].upper()
            quote = r["to"].upper()
            rate = r["rate"]

            base_cur, _ = FXCurrency.objects.get_or_create(code=base)
            quote_cur, _ = FXCurrency.objects.get_or_create(code=quote)

            FXRate.objects.update_or_create(
                from_currency=base_cur,
                to_currency=quote_cur,
                defaults={"rate": rate}
            )
            update += 1

        return updated

    @classmethod
    def sync_all_rates(cls):
        """
        Sync rates for EVERY forex pair that exists in FXRate table.
        """
        symbols = [
            f"{fx.from_currency.code}{fx.to_currency.code}"
            for fx in FXRate.objects.all()
        ]

        return cls.sync_rates_for_symbols(symbols)
