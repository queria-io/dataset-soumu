"""総務省のデータパイプライン。

1. plans: 行政事業レビューが挙げる計画・通知等の PDF を取得し、ページごとの本文の Parquet にする
2. local_finance: 市町村別決算状況調の Excel を取得し、セルの Parquet にする
3. code: 統計に用いる標準地域コードの CSV と Excel を取得し、行の NDJSON にする
4. dbt: dbt ビルド
"""

import logging

from dbt.cli.main import dbtRunner

from pipelines import area_code, municipal_settlement, plans

# dbt を読み込むとルートロガーが先に設定されるので、force で上書きする
logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
logger = logging.getLogger("pipelines")


def dbt_build():
    dbt = dbtRunner()
    for command in (["deps"], ["build"], ["docs", "generate"]):
        if not dbt.invoke(command).success:
            raise SystemExit(f"dbt {' '.join(command)} failed")


def main():
    logger.info("1/4: plans (行政事業レビューが挙げる計画・通知等)")
    plans.download_plans()
    plans.build_plans_parquet()
    logger.info("2/4: local_finance (市町村別決算状況調)")
    municipal_settlement.download()
    municipal_settlement.build_parquet()
    logger.info("3/4: code (統計に用いる標準地域コード)")
    area_code.build()
    logger.info("4/4: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
