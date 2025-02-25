# Copyright 2025 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl)

from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase


class PredictedExpiryDate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        #
        category = cls.env["product.category"].create(
            {
                "name": "Test Category",
                "removal_strategy_id": cls.env.ref("stock.removal_fifo").id,
                "packaging_reserve_method": "partial",
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product with Expiration Date",
                "use_expiration_date": True,
                "tracking": "lot",
                "categ_id": category.id,
                "type": "product",
            }
        )
        now = datetime.now()
        cls.high_exp_date = now + timedelta(days=10)
        cls.lower_exp_date = now + timedelta(days=5)
        cls.env["stock.quant"].create(
            {
                "product_id": cls.product.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "quantity": 10.0,
                "lot_id": cls.env["stock.lot"]
                .create(
                    {
                        "name": "Lot 1",
                        "product_id": cls.product.id,
                        "expiration_date": cls.high_exp_date,
                    }
                )
                .id,
            }
        )
        cls.env["stock.quant"].create(
            {
                "product_id": cls.product.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "quantity": 10.0,
                "lot_id": cls.env["stock.lot"]
                .create(
                    {
                        "name": "Lot 2",
                        "product_id": cls.product.id,
                        "expiration_date": cls.lower_exp_date,
                    }
                )
                .id,
            }
        )

    def _create_order(self):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 5.0,
                        },
                    )
                ],
            }
        )

    def test_predicted_expiry_date(self):
        # Fifo in order of creation
        sale1 = self._create_order()
        self.assertEqual(
            sale1.order_line.predicted_first_expiration_date, self.high_exp_date.date()
        )
        # Fefo in order of expiration date
        self.product.categ_id.removal_strategy_id = self.env.ref(
            "product_expiry.removal_fefo"
        )
        sale2 = self._create_order()
        self.assertEqual(
            sale2.order_line.predicted_first_expiration_date, self.lower_exp_date.date()
        )
