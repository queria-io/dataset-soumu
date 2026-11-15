"""総務省のデータパイプライン。

1. plans: 行政事業レビューが挙げる計画・通知等の PDF を取得し、ページごとの本文の Parquet にする
2. local_finance: 市町村別決算状況調の Excel を取得し、縦持ちの Parquet にする
3. dbt: dbt ビルド
"""

import logging

from dbt.cli.main import dbtRunner

from pipelines import municipal_settlement, plans

# dbt を読み込むとルートロガーが先に設定されるので、force で上書きする
logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
logger = logging.getLogger("pipelines")


def dbt_build():
    dbt = dbtRunner()
    for command in (["deps"], ["build"], ["docs", "generate"]):
        if not dbt.invoke(command).success:
            raise SystemExit(f"dbt {' '.join(command)} failed")


def main():
    logger.info("1/3: plans (行政事業レビューが挙げる計画・通知等)")
    plans.download_plans()
    plans.build_plans_parquet()
    logger.info("2/3: local_finance (市町村別決算状況調)")
    municipal_settlement.download()
    municipal_settlement.build_parquet()
    logger.info("3/3: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
