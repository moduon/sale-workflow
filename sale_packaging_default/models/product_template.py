# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    require_packaging = fields.Boolean(default=False)
