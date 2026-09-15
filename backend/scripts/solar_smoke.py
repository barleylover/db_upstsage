from __future__ import annotations

import os
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.domain.models import InterpretChangeRequest  # noqa: E402
from app.services.solar_client import UpstageSolarClient  # noqa: E402


def main() -> int:
    if not os.getenv("UPSTAGE_API_KEY"):
        print("SKIP: UPSTAGE_API_KEY is not configured")
        return 0
    payload = InterpretChangeRequest.model_validate(
        {
            "originalRequest": "tenant_id가 42이고 status가 pending인 주문을 cancelled로 변경해 주세요.",
            "schemaInput": {
                "database": "app",
                "schema": "public",
                "tables": [
                    {
                        "name": "orders",
                        "columns": [
                            {"name": "id", "dataType": "bigint", "nullable": False},
                            {"name": "tenant_id", "dataType": "bigint", "nullable": False},
                            {"name": "status", "dataType": "varchar", "nullable": False},
                        ],
                        "primaryKeyColumns": ["id"],
                    }
                ],
            },
        }
    )
    draft = UpstageSolarClient(get_settings()).interpret(payload)
    print(draft.model_dump_json(by_alias=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
