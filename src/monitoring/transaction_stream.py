"""
Simulated real-time transaction streaming generator.
Iterates transactions from dataset source or event payloads to simulate live banking stream.
"""

from typing import Generator, Dict, Any, List, Optional
import time
from src.data.ingestion import load_raw_dataset
from src.utils.logger import get_logger

logger = get_logger(__name__)


def generate_transaction_stream(
    batch_size: Optional[int] = None,
    delay_seconds: float = 0.5,
    source_df: Optional[Any] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Simulates a stream of live incoming financial transactions.

    Args:
        batch_size: Maximum number of transactions to stream (None for all).
        delay_seconds: Delay interval between stream events.
        source_df: Optional DataFrame source (loads raw CSV if None).

    Yields:
        Transaction dictionary payload.
    """
    logger.info(f"Starting simulated transaction stream (delay={delay_seconds}s)...")
    df = source_df if source_df is not None else load_raw_dataset()

    max_rows = len(df) if batch_size is None else min(batch_size, len(df))

    for idx in range(max_rows):
        row = df.iloc[idx]
        tx_payload = {
            "transaction_id": str(row["Transaction_ID"]),
            "customer_id": str(row["Customer_ID"]),
            "transaction_date": str(row["Transaction_Date"]),
            "transaction_amount": float(row["Transaction_Amount"]),
            "merchant_category": str(row["Merchant_Category"]),
            "payment_method": str(row["Payment_Method"]),
            "device_type": str(row["Device_Type"]),
            "location": str(row["Location"]),
            "is_international": int(row["Is_International"]),
            "previous_transactions": int(row["Previous_Transactions"]),
            "average_spend": float(row["Average_Spend"]),
            "account_age_days": int(row["Account_Age_Days"]),
            "suspicious_keyword": str(row["Suspicious_Keyword"]),
            "fraudulent": int(row["Fraudulent"]) if "Fraudulent" in row else None
        }

        yield tx_payload

        if delay_seconds > 0:
            time.sleep(delay_seconds)
