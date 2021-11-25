# Copyright 2021 OpenSynergy Indonesia
# Copyright 2021 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CommissionCommissionTax(models.Model):
    _name = "commission.commission_tax"
    _description = "Commission Tax"

    commission_id = fields.Many2one(
        string="# Commission",
        comodel_name="commission.commission",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(
        string="Sequence",
        required=True,
        default=5,
    )
    tax_id = fields.Many2one(
        string="Tax",
        required=True,
        ondelete="restrict",
        comodel_name="account.tax",
    )
    account_id = fields.Many2one(
        string="Account",
        required=True,
        ondelete="restrict",
        comodel_name="account.account",
    )
    amount_base = fields.Float(
        string="Base Amount",
        required=True,
    )
    amount_tax = fields.Float(
        string="Tax Amount",
        required=True,
    )
