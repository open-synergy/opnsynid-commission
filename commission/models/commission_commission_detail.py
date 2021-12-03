# Copyright 2021 OpenSynergy Indonesia
# Copyright 2021 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CommissionCommissionDetail(models.Model):
    _name = "commission.commission_detail"
    _description = "Commission Detail"

    @api.multi
    @api.depends("amount_before_tax", "tax_ids")
    def _compute_total(self):
        for record in self:
            total_amount = record.amount_before_tax
            taxes = False
            if record.tax_ids:
                taxes = record.tax_ids.compute_all(total_amount)
            record.amount_before_tax = (
                taxes["total_excluded"] if taxes else total_amount
            )
            record.amount_after_tax = (
                taxes["total_included"] if taxes else record.amount_before_tax
            )

    commission_id = fields.Many2one(
        string="# Commission",
        comodel_name="commission.commission",
        required=True,
        ondelete="cascade",
    )
    account_move_line_id = fields.Many2one(
        string="Account Move Line",
        comodel_name="account.move.line",
        required=True,
        ondelete="restrict",
    )
    account_id = fields.Many2one(
        string="Account",
        comodel_name="account.account",
        required=True,
        ondelete="restrict",
    )
    tax_ids = fields.Many2many(
        string="Tax",
        comodel_name="account.tax",
        relation="rel_commission_detail_2_tax",
        column1="line_id",
        column2="tax_id",
    )
    amount_before_tax = fields.Float(
        string="Amount Before Tax",
        required=True,
    )
    amount_after_tax = fields.Float(
        string="Amount After Tax", required=True, compute="_compute_total"
    )

    @api.multi
    def _prepare_move_line_detail(self):
        self.ensure_one()
        return (
            0,
            0,
            {
                "name": self.account_move_line_id.display_name,
                "account_id": self.account_id.id,
                "debit": self.amount_before_tax,
                "credit": 0.0,
                "amount_currency": self._get_amount_currency(),
                "currency_id": self._get_currency(),
            },
        )

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
