from analytics.models import AnalyticResult


class ResultWriterService:
    @staticmethod
    def replace_results_for_run(*, run, dimension_rows):
        AnalyticResult.objects.filter(run=run).delete()

        to_create = []

        for dimension, rows in dimension_rows:
            for row in rows:
                to_create.append(
                    AnalyticResult(
                        run=run,
                        dimension=dimension,
                        bucket_id=row["bucket_id"],
                        bucket_label_snapshot=row["bucket_label"],
                        total_value=row["total_value"],
                        percentage=row["percentage"],
                        holding_count=row["holding_count"],
                    )
                )

        if to_create:
            AnalyticResult.objects.bulk_create(to_create)

        return to_create
