"""Portal sub-module — endpoints consumed by the subscriber (customer) UI.

The current user is the customer. The subscriber row is resolved by
WaterSubscriber.user_id == user.id. Every query is scoped to that
subscriber, so a customer can never see data outside their own account.
"""
