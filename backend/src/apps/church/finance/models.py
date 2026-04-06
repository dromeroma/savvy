"""Church finance models — LEGACY.

Church income/expense data now lives in the shared `finance_transactions`
and `finance_categories` tables via SavvyFinance.  The old ChurchIncome,
ChurchExpense, and their category tables remain here solely to support
existing database migrations.  No new code should reference these models.
"""

# Legacy models preserved for migration history.  See:
#   src.modules.finance.models.FinanceTransaction
#   src.modules.finance.models.FinanceCategory
