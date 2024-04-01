class StoreNotReady(Exception):
    pass


class OutsideDeliveryRange(Exception):
    pass


class PurchaseNotFound(Exception):
    pass


class CantPurchaseFromOwnStore(Exception):
    pass
