# Copyright 2021 PT. Simetri Sinergi Indonesia
# Copyright 2021 OpenSynergy Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero


class CommissionCommission(models.Model):
    _name = "commission.commission"
    _description = "Commission"
    _inherit = [
        "mixin.sequence",
        "mail.thread",
        "mixin.policy",
        "mixin.multiple_approval",
    ]
    _approval_from_state = "draft"
    _approval_to_state = "open"
    _approval_state = "confirm"

    @api.depends(
        "type_id",
        "user_id",
        "date_start",
        "date_end",
    )
    def _compute_allowed_goal_ids(self):
        obj_goal = self.env["gamification.goal"]
        for record in self:
            result = definition_ids = []
            if (
                record.type_id
                and record.user_id
                and record.date_start
                and record.date_end
            ):
                for computation in record.type_id.computation_ids:
                    definition_ids.append(computation.definition_id.id)
                criteria = [
                    ("definition_id", "in", definition_ids),
                    ("user_id", "=", record.user_id.id),
                    ("start_date", ">=", record.date_start),
                    ("end_date", "<=", record.date_end),
                ]
                result = obj_goal.search(criteria).ids
            record.allowed_goal_ids = result

    @api.depends(
        "account_move_id",
    )
    def _compute_payable_move_line_id(self):
        for record in self:
            result = False
            if record.account_move_id:
                payable_move_lines = record.account_move_id.line_ids.filtered(
                    lambda r: r.account_id.id == record.payable_account_id.id
                )
                result = payable_move_lines[0].id
            record.payable_move_line_id = result

    @api.depends(
        "payable_move_line_id",
    )
    def _compute_payment_move_line_ids(self):
        obj_reconcile = self.env["account.partial.reconcile"]
        for record in self:
            result = []
            if record.payable_move_line_id:
                criteria = [("credit_move_id", "=", record.payable_move_line_id.id)]
                for reconcile in obj_reconcile.search(criteria):
                    result.append(reconcile.debit_move_id.id)
            record.payment_move_line_ids = result

    @api.depends(
        "payable_move_line_id",
        "payable_move_line_id.matched_debit_ids",
        "payable_move_line_id.matched_debit_ids.credit_move_id.date",
    )
    def _compute_last_payment(self):
        for record in self:
            result_move = result_date = False
            if record.payment_move_line_ids:
                result_move = record.payment_move_line_ids[0]
                result_date = result_move.date
            record.last_payment_move_line_id = result_move
            record.last_payment_date = result_date

    @api.depends(
        "payable_move_line_id",
        "payable_move_line_id.amount_residual",
    )
    def _compute_residual(self):
        for record in self:
            residual = 0.0
            reconciled = False
            if record.payable_move_line_id:
                residual = abs(record.payable_move_line_id.amount_residual)
                if float_is_zero(residual, precision_rounding=2):
                    reconciled = True
                else:
                    reconciled = False
            record.reconciled = reconciled
            record.amount_residual = residual

    @api.multi
    @api.depends(
        "type_id",
    )
    def _compute_allowed_journal_ids(self):
        obj_allowed = self.env["commission.type"]
        for comm_type in self:
            criteria = [
                ("id", "=", comm_type.type_id.id),
            ]
            journal_ids = obj_allowed.search(criteria).mapped(
                lambda r: r.allowed_payable_journal_ids
            )
            comm_type.allowed_journal_ids = journal_ids

    @api.multi
    @api.depends(
        "type_id",
    )
    def _compute_allowed_payable_account_ids(self):
        obj_allowed = self.env["commission.type"]
        for comm_type in self:
            criteria = [
                ("id", "=", comm_type.type_id.id),
            ]
            account_ids = obj_allowed.search(criteria).mapped(
                lambda r: r.allowed_payable_account_ids
            )
            comm_type.allowed_payable_account_ids = account_ids

    @api.multi
    @api.depends(
        "type_id",
        "detail_ids.amount_before_tax",
        "detail_ids.amount_after_tax",
        "tax_ids.amount_tax",
    )
    def _compute_amount(self):
        for commission in self:
            amount_before_tax = 0.0
            amount_tax = 0.0
            amount_after_tax = 0.0

            for line in commission.detail_ids:
                amount_before_tax += line.amount_before_tax
                amount_after_tax += line.amount_after_tax

            for tax in commission.tax_ids:
                amount_tax += tax.amount_tax

            commission.amount_before_tax = amount_before_tax
            commission.amount_tax = amount_tax
            commission.amount_after_tax = amount_after_tax

    @api.multi
    def _compute_policy(self):
        _super = super(CommissionCommission, self)
        _super._compute_policy()

    name = fields.Char(
        string="# Document",
        default="/",
        required=True,
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_commission = fields.Date(
        string="Commission Date",
        index=True,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=True,
        default=fields.Date.context_today,
    )
    date_start = fields.Date(
        string="Start Date",
        copy=True,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_end = fields.Date(
        string="End Date",
        copy=True,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_due = fields.Date(
        string="Date Due",
        copy=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    type_id = fields.Many2one(
        string="Type",
        copy=True,
        required=True,
        ondelete="restrict",
        comodel_name="commission.type",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    allowed_tax_ids = fields.Many2many(
        string="Allowed Tax(es)",
        comodel_name="account.tax",
        related="type_id.allowed_tax_ids",
        store=False,
    )
    user_id = fields.Many2one(
        string="Agent",
        copy=True,
        required=True,
        ondelete="restrict",
        comodel_name="res.users",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    allowed_goal_ids = fields.Many2many(
        string="Allowed Goals",
        comodel_name="gamification.goal",
        compute="_compute_allowed_goal_ids",
        store=False,
    )
    detail_ids = fields.One2many(
        string="Commission Detail",
        comodel_name="commission.commission_detail",
        inverse_name="commission_id",
        copy=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    tax_ids = fields.One2many(
        string="Tax",
        comodel_name="commission.commission_tax",
        inverse_name="commission_id",
        copy=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    note = fields.Text(
        string="Note",
        copy=True,
    )
    account_move_id = fields.Many2one(
        string="Account Move",
        comodel_name="account.move",
        ondelete="restrict",
        copy=False,
        readonly=True,
    )
    payable_move_line_id = fields.Many2one(
        string="Payable Journal Item",
        comodel_name="account.move.line",
        compute="_compute_payable_move_line_id",
        store=True,
    )
    payment_move_line_ids = fields.Many2many(
        string="Payment Journal Items",
        comodel_name="account.move.line",
        compute="_compute_payment_move_line_ids",
    )
    last_payment_move_line_id = fields.Many2one(
        string="Last Payment Move Line",
        comodel_name="account.move.line",
        compute="_compute_last_payment",
        store=True,
    )
    last_payment_date = fields.Date(
        string="Last Payment Date",
        compute="_compute_last_payment",
        store=True,
    )
    reconciled = fields.Boolean(
        string="Reconciled",
        compute="_compute_residual",
        store=True,
    )
    amount_residual = fields.Float(
        string="Amount Residual",
        compute="_compute_residual",
        store=True,
    )
    allowed_payable_account_ids = fields.Many2many(
        string="Allowed Payable Account",
        comodel_name="account.account",
        compute="_compute_allowed_payable_account_ids",
    )

    payable_account_id = fields.Many2one(
        string="Account Payable",
        required=True,
        ondelete="restrict",
        comodel_name="account.account",
        copy=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    allowed_journal_ids = fields.Many2many(
        string="Allowed Journal",
        comodel_name="account.journal",
        compute="_compute_allowed_journal_ids",
    )
    journal_id = fields.Many2one(
        string="Journal",
        required=True,
        ondelete="restrict",
        comodel_name="account.journal",
        copy=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    amount_before_tax = fields.Float(
        string="Total Amount Before Tax",
        store=True,
        compute="_compute_amount",
    )
    amount_tax = fields.Float(
        string="Tax Amount",
        store=True,
        compute="_compute_amount",
    )
    amount_after_tax = fields.Float(
        string="Total Amount After Tax",
        store=True,
        compute="_compute_amount",
    )

    state = fields.Selection(
        string="State",
        selection=[
            ("draft", "Draft"),
            ("confirm", "Waiting for Approval"),
            ("open", "Waiting for Payments"),
            ("done", "Paid"),
            ("cancel", "Cancelled"),
            ("reject", "Rejected"),
        ],
        default="draft",
        copy=False,
    )

    # Policy Field
    confirm_ok = fields.Boolean(
        string="Can Confirm",
        compute="_compute_policy",
    )
    open_ok = fields.Boolean(
        string="Can Open",
        compute="_compute_policy",
    )
    cancel_ok = fields.Boolean(
        string="Can Cancel",
        compute="_compute_policy",
    )
    restart_ok = fields.Boolean(
        string="Can Restart",
        compute="_compute_policy",
    )

    @api.multi
    def _write(self, vals):
        pre_not_reconciled = self.filtered(lambda r: not r.reconciled)
        pre_reconciled = self - pre_not_reconciled
        res = super(CommissionCommission, self)._write(vals)
        reconciled = self.filtered(lambda r: r.reconciled)
        not_reconciled = self - reconciled
        (reconciled & pre_reconciled).filtered(
            lambda r: r.state == "open"
        ).action_done()
        (not_reconciled & pre_not_reconciled).filtered(
            lambda r: r.state == "done"
        ).action_reopen()
        return res

    @api.multi
    def _prepare_confirm_data(self):
        self.ensure_one()
        return {
            "state": "confirm",
        }

    @api.multi
    def action_confirm(self):
        for document in self:
            document.write(document._prepare_confirm_data())
            document.action_request_approval()

    @api.multi
    def action_reopen(self):
        for document in self:
            document.write(document._prepare_reopen_data())

    @api.multi
    def _prepare_open_data(self):
        self.ensure_one()
        move = self._create_accounting_entry()
        return {
            "state": "open",
            "account_move_id": move.id,
        }

    @api.multi
    def _prepare_reopen_data(self):
        self.ensure_one()
        return {
            "state": "open",
        }

    @api.multi
    def _create_accounting_entry(self):
        self.ensure_one()
        if not self.detail_ids:
            raise UserError(_("Please create some detail lines."))
        return self.env["account.move"].create(self._prepare_account_move())

    @api.multi
    def _prepare_account_move(self):
        self.ensure_one()
        return {
            "name": self.name,
            "ref": self.name,
            "journal_id": self.journal_id.id,
            "date": self.date_commission,
            "line_ids": self._prepare_move_line(),
        }

    @api.multi
    def _prepare_move_line(self):
        self.ensure_one()
        result = []
        result += self._prepare_move_line_payable()
        result += self._prepare_move_line_detail()
        result += self._prepare_move_line_tax()
        return result

    @api.multi
    def _get_partner(self):
        self.ensure_one()
        result = self.user_id.partner_id
        if self.user_id.partner_id.contact_id:
            result = self.user_id.partner_id.contact_id
        return result

    @api.multi
    def _prepare_move_line_payable(self):
        self.ensure_one()
        return [
            (
                0,
                0,
                {
                    "name": self.name,
                    "account_id": self.payable_account_id.id,
                    "partner_id": self._get_partner().id,
                    "debit": 0.0,
                    "credit": self.amount_after_tax,
                    "amount_currency": self._get_payable_amount_currency(),
                    "currency_id": self._get_currency(),
                    "date_maturity": self._get_date_due(),
                },
            )
        ]

    @api.multi
    def _get_date_due(self):
        self.ensure_one()
        result = fields.Date.today()
        if self.date_due:
            result = self.date_due
        return result

    @api.multi
    def _get_payable_amount_currency(self):
        self.ensure_one()
        return 0.0

    # TODO

    @api.multi
    def _get_currency(self):
        self.ensure_one()
        return False

    # TODO

    @api.multi
    def _prepare_move_line_detail(self):
        self.ensure_one()
        # loop on detail_ids
        result = []
        for detail in self.detail_ids:
            result.append(detail._prepare_move_line_detail())
        return result

    @api.multi
    def _prepare_move_line_tax(self):
        self.ensure_one()
        # loop on tax_ids
        result = []
        for tax in self.tax_ids:
            result.append(tax._prepare_move_line_tax())
        return result

    @api.multi
    def action_open(self):
        for document in self:
            document.write(document._prepare_open_data())

    @api.multi
    def _prepare_done_data(self):
        self.ensure_one()
        return {
            "state": "done",
        }

    @api.multi
    def action_done(self):
        for document in self:
            document.write(document._prepare_done_data())

    @api.multi
    def _prepare_cancel_data(self):
        self.ensure_one()
        return {
            "state": "cancel",
        }

    @api.multi
    def action_cancel(self):
        for document in self:
            document.write(document._prepare_cancel_data())

    @api.multi
    def _prepare_restart_data(self):
        self.ensure_one()
        return {
            "state": "draft",
        }

    @api.multi
    def action_restart(self):
        for document in self:
            document.write(document._prepare_restart_data())

    def action_approve_approval(self):
        _super = super(CommissionCommission, self)
        _super.action_approve_approval()
        for document in self:
            if document.approved:
                document.action_open()

    @api.multi
    def action_populate_detail(self):
        for document in self:
            document._populate_detail()

    @api.multi
    def _populate_detail(self):
        self.ensure_one()
        self.detail_ids.unlink()
        self.tax_ids.unlink()
        self.write(self._prepare_populate_detail())

    @api.multi
    def _prepare_populate_detail(self):
        self.ensure_one()
        return {
            "detail_ids": self._prepare_detail(),
        }

    @api.multi
    def _prepare_detail(self):
        self.ensure_one()
        result = []
        obj_detail = self.env["commission.commission_detail"]
        for goal in self.allowed_goal_ids:
            detail_cache = obj_detail.new(
                {
                    "commission_id": self.id,
                    "goal_id": goal.id,
                }
            )
            detail_cache._compute_computation_id()
            detail_cache.onchange_account_id()
            detail_cache.onchange_amount_fixed()
            detail_cache.onchange_amount_percentage()
            detail_cache.onchange_amount_base()
            values = detail_cache._convert_to_write(detail_cache._cache)
            result.append((0, 0, values))
        return result

    @api.onchange(
        "type_id",
    )
    def onchange_policy_template_id(self):
        template_id = self._get_template_policy()
        self.policy_template_id = template_id

    @api.onchange(
        "type_id",
    )
    def onchange_payable_account(self):
        self.payable_account_id = False
        if self.type_id:
            obj_allowed = self.env["commission.type"]
            for comm_type in self:
                criteria = [
                    ("id", "=", comm_type.type_id.id),
                ]
                payable_account = obj_allowed.search(criteria).mapped(
                    lambda r: r.default_payable_account_id
                )
                comm_type.payable_account_id = payable_account

    @api.onchange(
        "type_id",
    )
    def onchange_journal(self):
        self.journal_id = False
        if self.type_id:
            obj_allowed = self.env["commission.type"]
            for comm_type in self:
                criteria = [
                    ("id", "=", comm_type.type_id.id),
                ]
                journal = obj_allowed.search(criteria).mapped(
                    lambda r: r.payable_journal_id
                )
                comm_type.journal_id = journal

    @api.onchange("detail_ids")
    def onchange_tax_ids(self):
        taxes_grouped = self.get_taxes_values()
        tax_lines = self.env["commission.commission_tax"]
        for tax in taxes_grouped.values():
            tax_lines += tax_lines.new(tax)
        self.tax_ids = tax_lines

    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        cur = self.env.ref("base.USD")
        round_curr = cur.round
        for line in self.detail_ids:
            price_unit = line.amount_before_tax
            taxes = line.tax_ids.compute_all(price_unit, cur, 1.0)["taxes"]
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env["account.tax"].browse(tax["id"]).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                    tax_grouped[key]["amount_base"] = round_curr(val["amount_base"])
                else:
                    tax_grouped[key]["amount_tax"] += val["amount_tax"]
                    tax_grouped[key]["amount_base"] += round_curr(val["amount_base"])
        return tax_grouped

    def _prepare_tax_line_vals(self, line, tax):
        vals = {
            "commission_id": self.id,
            "name": tax["name"],
            "tax_id": tax["id"],
            "amount_tax": tax["amount"],
            "amount_base": tax["base"],
            "manual": False,
            "sequence": tax["sequence"],
            "account_id": tax["account_id"],
            "account_analytic_id": False,
        }
        return vals

    @api.model
    def create(self, values):
        _super = super(CommissionCommission, self)
        result = _super.create(values)
        sequence = result._create_sequence()
        result.write(
            {
                "name": sequence,
            }
        )
        return result

    @api.multi
    @api.constrains("date_start", "date_end")
    def _check_start_end_date(self):
        for record in self:
            if record.date_start:
                if record.date_end:
                    if record.date_start >= record.date_end:
                        msg = _("End Date must bigger than Start Date")
                        raise ValidationError(msg)
