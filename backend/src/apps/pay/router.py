"""SavvyPay app router — financial infrastructure backbone."""

from fastapi import APIRouter
from src.apps.pay.ledger.router import router as ledger_router
from src.apps.pay.transactions.router import router as transactions_router
from src.apps.pay.wallets.router import router as wallets_router
from src.apps.pay.fees.router import router as fees_router
from src.apps.pay.payouts.router import router as payouts_router
from src.apps.pay.subscriptions.router import router as subscriptions_router
from src.apps.pay.dashboard.router import router as dashboard_router

router = APIRouter(prefix="/pay", tags=["SavvyPay"])

router.include_router(dashboard_router)
router.include_router(ledger_router)
router.include_router(transactions_router)
router.include_router(wallets_router)
router.include_router(fees_router)
router.include_router(payouts_router)
router.include_router(subscriptions_router)
