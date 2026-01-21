from schemas.seed.equity import equity_schema_template
from schemas.seed.crypto import crypto_schema_template
from schemas.seed.precious_metal import precious_metals_schema_template


def get_all_schema_templates():
    return [
        equity_schema_template(),
        crypto_schema_template(),
        precious_metals_schema_template(),
    ]
