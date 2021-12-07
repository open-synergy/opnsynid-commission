# Copyright 2021 PT. Simetri Sinergi Indonesia
# Copyright 2021 OpenSynergy Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


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

    name = fields.Char(
        string="# Document",
        default="/",
        required=True,
    )
    date_commission = fields.Date(
        string="Commission Date",
        index=True,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
        default=fields.Date.context_today,
    )
    date_start = fields.Date(
        string="Start Date",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_end = fields.Date(
        string="End Date",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    type_id = fields.Many2one(
        string="Type",
        required=True,
        ondelete="restrict",
        comodel_name="commission.type",
    )
    user_id = fields.Many2one(
        string="Agent",
        required=True,
        ondelete="restrict",
        comodel_name="res.users",
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
    )
    tax_ids = fields.One2many(
        string="Tax",
        comodel_name="commission.commission_tax",
        inverse_name="commission_id",
    )
    note = fields.Text(
        string="Note",
    )
    account_move_id = fields.Many2one(
        string="Account Move",
        readonly=True,
        ondelete="restrict",
        comodel_name="account.move",
    )
    allowed_payable_account_ids = fields.Many2many(
        string="Allowed Payable Account",
        comodel_name="account.account",
        compute="_compute_allowed_payable_account_ids",
    )

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

    payable_account_id = fields.Many2one(
        string="Account Payable",
        required=True,
        ondelete="restrict",
        comodel_name="account.account",
    )
    allowed_journal_ids = fields.Many2many(
        string="Allowed Journal",
        comodel_name="account.journal",
        compute="_compute_allowed_journal_ids",
    )

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

    journal_id = fields.Many2one(
        string="Journal",
        required=True,
        ondelete="restrict",
        comodel_name="account.journal",
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

    state = fields.Selection(
        string="State",
        selection=[
            ("draft", "Draft"),
            ("confirm", "Waiting for Approval"),
            ("open", "On Progress"),
            ("done", "Finished"),
            ("cancel", "Cancelled"),
            ("reject", "Rejected"),
        ],
        default="draft",
    )

    @api.multi
    def _compute_policy(self):
        _super = super(CommissionCommission, self)
        _super._compute_policy()

    # Policy Field
    confirm_ok = fields.Boolean(
        string="Can Confirm",
        compute="_compute_policy",
    )
    open_ok = fields.Boolean(
        string="Can Open",
        compute="_compute_policy",
    )
    done_ok = fields.Boolean(
        string="Can Finish",
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
    def _prepare_open_data(self):
        self.ensure_one()
        move = self._create_accounting_entry()
        return {
            "state": "open",
            "account_move_id": move.id,
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
    def _prepare_move_line_payable(self):
        # Only 1 data
        self.ensure_one()
        return [
            (
                0,
                0,
                {
                    "name": self.name,
                    "account_id": self.payable_account_id.id,
                    "debit": 0.0,
                    "credit": self.amount_after_tax,
                    "amount_currency": self._get_payable_amount_currency(),
                    "currency_id": self._get_currency(),
                },
            )
        ]

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
        return

    @api.onchange(
        "type_id",
    )
    def onchange_policy_template_id(self):
        template_id = self._get_template_policy()
        for document in self:
            document.policy_template_id = template_id

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
        if self.date_start:
            if self.date_end:
                if self.date_start >= self.date_end:
                    msg = _("End Date must bigger than Start Date")
                    raise ValidationError(msg)
