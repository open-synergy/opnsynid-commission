# Copyright 2021 OpenSynergy Indonesia
# Copyright 2021 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CommissionType(models.Model):
    _name = "commission.type"
    _description = "Commission Type"

    name = fields.Char(
        string="Commission Type",
        required=True,
    )
    code = fields.Char(
        string="Code",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
    )
    description = fields.Text(
        string="Description",
    )
    default_payable_account_id = fields.Many2one(
        string="Default Payable Account",
        comodel_name="account.account",
    )
    allowed_payable_account_ids = fields.Many2many(
        string="Allowed Payable Account",
        comodel_name="account.account",
        relation="rel_commission_type_2_payable_account",
        column1="type_id",
        column2="account_id",
    )
    payable_journal_id = fields.Many2one(
        string="Payable Journal",
        comodel_name="account.journal",
    )
    allowed_payable_journal_ids = fields.Many2many(
        string="Allowed Payable Journal",
        comodel_name="account.journal",
        relation="rel_commission_type_2_journal",
        column1="type_id",
        column2="journal_id",
    )
    tax_ids = fields.Many2many(
        string="Tax",
        comodel_name="account.tax",
        relation="rel_commission_type_2_tax",
        column1="type_id",
        column2="tax_id",
    )
    computation_ids = fields.One2many(
        string="Computations",
        comodel_name="commission.type_computation",
        inverse_name="type_id",
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
