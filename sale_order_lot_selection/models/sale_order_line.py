from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    lot_id = fields.Many2one("stock.production.lot", "Lot", copy=False)

    def _prepare_procurement_values(self, group_id=False):
        vals = super()._prepare_procurement_values(group_id=group_id)
        if self.lot_id:
            vals["restrict_lot_id"] = self.lot_id.id
        return vals

    @api.onchange("product_id")
    def product_id_change(self):
        res = super().product_id_change()
        self.lot_id = False
        return res
