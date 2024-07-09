from typing import Optional
from pydantic import BaseModel

# Add your credentials:
# Add your client ID and secret
PP_CLIENT = 'Adgb6ViqcE5GTm'
PP_SECRET = 'ELXHWz-a5RbXnIHs1gTpaT'
PAYPAL_API = 'https://api-m.sandbox.paypal.com'

class Order(BaseModel):
    order_id: Optional[int] = 0
    session_id: str
    account_name: Optional[str] = ''
    item_type: str
    item_id: int
    value: float
    payment_completed: Optional[bool] = False

class PayPalManager:
    def __init__(self):
        self.paypal_orders = {} # FIXME: Esto se deberia guardar en la base de datos-
        self.paypal_order_id_counter = 0 # FIXME: Esto deberia un identificador globalmente unico.

    def create_order(self, order):
        print('create_order: ', order)
        order.order_id = self.paypal_order_id_counter
        order.payment_completed = False
        self.paypal_orders[order.order_id] = order
        self.paypal_order_id_counter += 1
        return order.json() # {'session_id': session_id, 'value': value}

    def payment_canceled_or_error(self, order):
        print('payment_canceled_or_error: ', order)
        self.paypal_orders.pop(order.order_id, None)
        print('Incomplete orders: ', len([(_k, v) for (_k, v) in self.paypal_orders.items() if v['payment_completed'] == False]))
        return order.json()

    def payment_completed(self, order):
        print('payment_completed: ', order)
        order.payment_completed = True
        print('Incomplete orders: ', len([(_k, v) for (_k, v) in self.paypal_orders.items() if v['payment_completed'] == False]))
        return order.json()
