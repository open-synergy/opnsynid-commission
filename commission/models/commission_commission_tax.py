# Copyright 2021 OpenSynergy Indonesia
# Copyright 2021 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


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

    @api.multi
    def _prepare_move_line_tax(self):
        self.ensure_one()
        return (
            0,
            0,
            {
                "name": self.tax_id.name,
                "account_id": self.account_id.id,
                "debit": self._get_debit(),
                "credit": self._get_credit(),
                "amount_currency": self._get_amount_currency(),
                "currency_id": self._get_currency(),
            },
        )

    @api.multi
    def _get_credit(self):
        self.ensure_one()
        credit = 0.0
        if self.amount_tax < 0.0:
            credit = self.amount_tax
        return credit

    @api.multi
    def _get_debit(self):
        self.ensure_one()
        debit = 0.0
        if self.amount_tax >= 0.0:
            debit = self.amount_tax
        return debit

    @api.multi
    def _get_amount_currency(self):
        self.ensure_one()
        return 0.0
        # TODO

    @api.multi
    def _get_currency(self):
        self.ensure_one()
        return False
        # TODO
