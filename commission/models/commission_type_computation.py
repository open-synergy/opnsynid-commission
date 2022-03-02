# Copyright 2021 OpenSynergy Indonesia
# Copyright 2021 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons import decimal_precision as dp


class CommissionTypeComputation(models.Model):
    _name = "commission.type_computation"
    _description = "Commission Type Computation"

    type_id = fields.Many2one(
        string="Type",
        comodel_name="commission.type",
        required=True,
        ondelete="cascade",
    )
    definition_id = fields.Many2one(
        string="Gamification Goal Definition",
        comodel_name="gamification.goal.definition",
        required=True,
    )
    account_id = fields.Many2one(
        string="Account",
        comodel_name="account.account",
        domain=[
            ("user_type_id.type", "=", "other"),
        ],
    )
    tax_ids = fields.Many2many(
        string="Default Tax(es)",
        comodel_name="account.tax",
        relation="rel_commission_type_computation_2_tax",
        column1="computation_id",
        column2="tax_id",
    )
    based_on = fields.Selection(
        string="Commission Computation Based On",
        selection=[
            ("current", "Current Value"),
            ("target", "Target Value"),
        ],
        required=True,
        default="current",
    )
    amount_percentage = fields.Float(
        string="Percentage",
        required=True,
        default=1.0,
        digits=dp.get_precision("Commission Percentage"),
    )
    amount_fixed = fields.Float(
        string="Fixed Amount",
        required=True,
        default=1.0,
    )
