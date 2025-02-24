# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_round


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    product_packaging_qty = fields.Float(
        string="Package quantity",
        compute="_compute_product_packaging_qty",
        inverse="_inverse_product_packaging_qty",
        digits="Product Unit of Measure",
    )

    @api.depends(
        "product_uom_qty", "product_uom", "product_packaging", "product_packaging.qty"
    )
    def _compute_product_packaging_qty(self):
        for sol in self:
            if (
                not sol.product_packaging
                or sol.product_uom_qty == 0
                or sol.product_packaging.qty == 0
            ):
                sol.product_packaging_qty = 0
                continue
            # Consider uom
            if sol.product_id.uom_id != sol.product_uom:
                product_qty = sol.product_uom._compute_quantity(
                    sol.product_uom_qty, sol.product_id.uom_id
                )
            else:
                product_qty = sol.product_uom_qty
            # Provide default values in case of missing product.
            # Odoo does not prevent you to modify product packaging
            # that are already linked to a sale order.
            # If by chance the product is removed (yes, you can do it)
            # this computation will be broken w/out this default.
            precision = sol.product_packaging.product_uom_id.rounding or 0.01
            qty_mod = float_round(
                product_qty % sol.product_packaging.qty,
                precision_rounding=precision,
            )
            # After the rounding, the value could be equals to sol.product_packaging.qty
            # So just re-apply the '%'
            qty_mod = qty_mod % sol.product_packaging.qty
            if not float_is_zero(
                qty_mod,
                precision_digits=precision,
            ):
                # If qty does not fit in package reset package qty
                sol.product_packaging_qty = 0
            else:
                # Maybe that product_packaging_qty should be an Integer, no ?
                qty = product_qty / sol.product_packaging.qty
                sol.product_packaging_qty = qty

    def _prepare_product_packaging_qty_values(self):
        return {
            "product_uom_qty": self.product_packaging.qty * self.product_packaging_qty,
            "product_uom": self.product_packaging.product_uom_id.id,
        }

    def _inverse_product_packaging_qty(self):
        for sol in self:
            if sol.product_packaging_qty and not sol.product_packaging:
                raise UserError(
                    _(
                        "You must define a package before setting a quantity "
                        "of said package."
                    )
                )
            if sol.product_packaging and sol.product_packaging.qty == 0:
                raise UserError(
                    _("Please select a packaging with a quantity bigger than 0")
                )
            if sol.product_packaging and sol.product_packaging_qty:
                sol.write(sol._prepare_product_packaging_qty_values())

    @api.onchange("product_packaging_qty")
    def _onchange_product_packaging_qty(self):
        if self.product_packaging and self.product_packaging_qty:
            self.update(self._prepare_product_packaging_qty_values())

    @api.onchange("product_packaging")
    def _onchange_product_packaging(self):
        if self.product_packaging:
            pack_qty = 1
            product_qty = self.product_packaging.qty
            if self.product_uom_qty > 0 and product_qty > 0:
                if (self.product_uom_qty % self.product_packaging.qty) == 0:
                    pack_qty = self.product_uom_qty / self.product_packaging.qty
                    product_qty = self.product_uom_qty
            self.update(
                {
                    "product_packaging_qty": pack_qty,
                    "product_uom_qty": product_qty,
                    "product_uom": self.product_id.uom_id,
                }
            )
        else:
            self.update({"product_packaging_qty": 0})
        return super()._onchange_product_packaging()
