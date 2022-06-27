# Copyright 2021 OpenSynergy Indonesia
# Copyright 2021 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class GenerateCommission(models.TransientModel):
    _name = "commission.generate_commission"
    _description = "Generate Commission"

    @api.model
    def _default_type_id(self):
        return self.env.context.get("active_id", False)

    type_id = fields.Many2one(
        string="Commission Type",
        comodel_name="commission.type",
        required=True,
        default=lambda self: self._default_type_id(),
    )
    date_start = fields.Date(
        string="Start Date",
        required=True,
    )
    date_end = fields.Date(
        string="End Date",
        required=True,
    )
    user_ids = fields.Many2many(
        string="Agents",
        comodel_name="res.users",
        relation="rel_generate_commission_2_user",
        column1="type_id",
        column2="user_id",
    )

    @api.multi
    def action_confirm(self):
        for record in self:
            record._generate_commission()

    @api.onchange(
        "type_id",
    )
    def onchange_user_ids(self):
        self.user_ids = False
        if self.type_id:
            self.user_ids = self.type_id.user_ids.ids

    @api.multi
    def _generate_commission(self):
        self.ensure_one()
        Commission = self.env["commission.commission"]
        for user in self.user_ids:
            commission = Commission.create(
                {
                    "user_id": user.id,
                    "type_id": self.type_id.id,
                    "date_commission": self.date_end,
                    "date_start": self.date_start,
                    "date_end": self.date_end,
                    "payable_account_id": self.type_id.default_payable_account_id.id,
                    "journal_id": self.type_id.payable_journal_id.id,
                }
            )
            commission.action_populate_detail()
