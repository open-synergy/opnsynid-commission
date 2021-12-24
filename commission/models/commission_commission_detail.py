# Copyright 2021 OpenSynergy Indonesia
# Copyright 2021 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CommissionCommissionDetail(models.Model):
    _name = "commission.commission_detail"
    _description = "Commission Detail"

    @api.multi
    @api.depends(
        "amount_base",
        "amount_percentage",
        "amount_fixed",
        "tax_ids",
    )
    def _compute_total(self):
        for record in self:
            total_amount = (
                record.amount_base * record.amount_percentage
            ) + record.amount_fixed
            taxes = False
            if record.tax_ids:
                taxes = record.tax_ids.compute_all(total_amount)
            record.amount_before_tax = (
                taxes["total_excluded"] if taxes else total_amount
            )
            record.amount_after_tax = (
                taxes["total_included"] if taxes else record.amount_before_tax
            )

    @api.depends(
        "goal_id",
    )
    def _compute_computation_id(self):
        for record in self:
            result = False
            obj_computation = self.env["commission.type_computation"]
            if record.goal_id:
                criteria = [
                    ("definition_id", "=", record.goal_id.definition_id.id),
                    ("type_id", "=", record.commission_id.type_id.id),
                ]
                computations = obj_computation.search(criteria)
                if len(computations) > 0:
                    result = computations[0].id
            record.computation_id = result

    commission_id = fields.Many2one(
        string="# Commission",
        comodel_name="commission.commission",
        required=True,
        ondelete="cascade",
    )
    computation_id = fields.Many2one(
        string="Computation",
        comodel_name="commission.type_computation",
        compute="_compute_computation_id",
        store=True,
    )
    goal_id = fields.Many2one(
        string="Gamification Goal",
        comodel_name="gamification.goal",
        ondelete="restrict",
    )
    date_start = fields.Date(
        string="Date Start",
        related="goal_id.start_date",
        store=True,
    )
    date_end = fields.Date(
        string="Date End",
        related="goal_id.end_date",
        store=True,
    )
    account_id = fields.Many2one(
        string="Account",
        comodel_name="account.account",
        required=True,
        ondelete="restrict",
    )
    analytic_account_id = fields.Many2one(
        string="Analytic Account",
        comodel_name="account.analytic.account",
        ondelete="restrict",
    )
    tax_ids = fields.Many2many(
        string="Tax",
        comodel_name="account.tax",
        relation="rel_commission_detail_2_tax",
        column1="line_id",
        column2="tax_id",
    )
    amount_base = fields.Float(
        string="Base Computation",
        required=True,
        default=0.0,
    )
    amount_percentage = fields.Float(
        string="Percentage",
        required=True,
        default=1.0,
    )
    amount_fixed = fields.Float(
        string="Fixed Amount",
        required=True,
        default=0.0,
    )
    amount_before_tax = fields.Float(
        string="Amount Before Tax",
        compute="_compute_total",
        store=True,
    )
    amount_after_tax = fields.Float(
        string="Amount After Tax",
        compute="_compute_total",
        store=True,
    )

    @api.multi
    def _prepare_move_line_detail(self):
        self.ensure_one()
        analytic = self._get_analytic_account()
        return (
            0,
            0,
            {
                "name": "TODO",
                "account_id": self.account_id.id,
                "debit": self.amount_before_tax,
                "credit": 0.0,
                "amount_currency": self._get_amount_currency(),
                "currency_id": self._get_currency(),
                "analytic_account_id": analytic and analytic.id or False,
            },
        )

    @api.multi
    def _get_analytic_account(self):
        self.ensure_one()
        return self.analytic_account_id or False

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

    @api.onchange(
        "goal_id",
        "computation_id",
    )
    def onchange_amount_base(self):
        result = 0.0
        if self.goal_id and self.computation_id:
            computation = self.computation_id
            if computation.based_on == "current":
                result = self.goal_id.current
            elif computation.based_on == "target":
                result = self.goal_id.target_goal
        self.amount_base = result

    @api.onchange(
        "goal_id",
        "computation_id",
    )
    def onchange_amount_percentage(self):
        result = 0.0
        if self.goal_id and self.computation_id:
            computation = self.computation_id
            result = computation.amount_percentage
        self.amount_percentage = result

    @api.onchange(
        "goal_id",
        "computation_id",
    )
    def onchange_amount_fixed(self):
        result = 0.0
        if self.goal_id and self.computation_id:
            computation = self.computation_id
            result = computation.amount_fixed
        self.amount_fixed = result

    @api.onchange(
        "goal_id",
        "computation_id",
    )
    def onchange_account_id(self):
        result = 0.0
        if self.goal_id and self.computation_id:
            computation = self.computation_id
            result = computation.account_id
        self.account_id = result
