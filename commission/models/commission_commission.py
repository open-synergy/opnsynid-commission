# Copyright 2021 PT. Simetri Sinergi Indonesia
# Copyright 2021 OpenSynergy Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class CommissionCommission(models.Model):
    _name = "commission.commission"
    _inherit = [
        "mixin.sequence",
        "mail.thread",
        "mixin.policy",
        "mixin.multiple_approval",
    ]
    _approval_from_state = "draft"
    _approval_to_state = "open"
    _approval_state = "confirm"

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
        state={"draft": [("readonly", False)]},
        copy=False,
        default=fields.Date.context_today,
    )
    date_start = fields.Date(
        string="Start Date",
        required=True,
        readonly=True,
        state={"draft": [("readonly", False)]},
    )
    date_end = fields.Date(
        string="End Date",
        required=True,
        readonly=True,
        state={"draft": [("readonly", False)]},
    )
    type_id = fields.Many2one(
        string="Type",
        required=True,
        ondelete="restrict",
        comodel_name="commission.type",
    )
    partner_id = fields.Many2one(
        string="Partner",
        required=True,
        ondelete="restrict",
        comodel_name="res.partner",
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
    # print_ok = fields.Boolean(
    #     string="Can Print",
    #     compute="_compute_policy",
    # )
    # smart_ok = fields.Boolean(
    #     string="Can Open Smart Button",
    #     compute="_compute_policy",
    # )

    # Log Fields
    confirm_date = fields.Datetime(
        string="Confirm Date",
        readonly=True,
        copy=False,
    )
    confirm_user_id = fields.Many2one(
        string="Confirmed By",
        comodel_name="res.users",
        readonly=True,
        copy=False,
    )
    open_date = fields.Datetime(
        string="Open Date",
        readonly=True,
        copy=False,
    )
    open_user_id = fields.Many2one(
        string="Opened By",
        comodel_name="res.users",
        readonly=True,
        copy=False,
    )
    done_date = fields.Datetime(
        string="Finish Date",
        readonly=True,
        copy=False,
    )
    done_user_id = fields.Many2one(
        string="Finished By",
        comodel_name="res.users",
        readonly=True,
        copy=False,
    )
    cancel_date = fields.Datetime(
        string="Cancel Date",
        readonly=True,
        copy=False,
    )
    cancel_user_id = fields.Many2one(
        string="Cancelled By",
        comodel_name="res.users",
        readonly=True,
        copy=False,
    )

    @api.multi
    def _prepare_confirm_data(self):
        self.ensure_one()
        return {
            "state": "confirm",
            "confirm_date": fields.Datetime.now(),
            "confirm_user_id": self.env.user.id,
        }

    @api.multi
    def action_confirm(self):
        for document in self:
            document.write(document._prepare_confirm_data())

    @api.multi
    def _prepare_open_data(self):
        self.ensure_one()
        return {
            "state": "open",
            "open_date": fields.Datetime.now(),
            "open_user_id": self.env.user.id,
        }

    @api.multi
    def action_open(self):
        for document in self:
            document.write(document._prepare_open_data())

    @api.multi
    def _prepare_done_data(self):
        self.ensure_one()
        return {
            "state": "done",
            "done_date": fields.Datetime.now(),
            "done_user_id": self.env.user.id,
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
            "cancel_date": fields.Datetime.now(),
            "cancel_user_id": self.env.user.id,
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
            "confirm_date": False,
            "confirm_user_id": False,
            "open_date": False,
            "open_user_id": False,
            "done_date": False,
            "done_user_id": False,
            "cancel_date": False,
            "cancel_user_id": False,
        }

    @api.multi
    def action_restart(self):
        for document in self:
            document.write(document._prepare_restart_data())

    # @api.multi
    # def action_print(self):
    #     for document in self:
    #         msg = _("Print status for %s: OK!") % document.name
    #         raise UserError(msg)

    # @api.multi
    # def action_open_smart_button(self):
    #     for document in self:
    #         msg = _("Open Smart Button status for %s: OK!") % document.name
    #         raise UserError(msg)

    @api.multi
    def action_populate_detail(self):
        return

    @api.onchange(
        "type_id",
    )
    def onchange_policy_template_id(self):
        template_id = self._get_template_id()
        for document in self:
            document.policy_template_id = template_id

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

            amount_tax = amount_before_tax - amount_after_tax
            commission.amount_before_tax = amount_before_tax
            commission.amount_after_tax = amount_after_tax
            commission.amount_tax = amount_tax

    @api.multi
    @api.depends(
        "type_id",
    )
    def _compute_allowed_journal_ids(self):
        obj_allowed = self.env["commission.type"]
        for comm_type in self:
            journal_ids = self.env["account.journal"].search([]).ids
            criteria = [
                ("id", "=", comm_type.type_id.id),
                # ("allowed_payable_journal_ids", "in", journal_ids),
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
            account_ids = self.env["account.account"].search([]).ids
            criteria = [
                ("id", "=", comm_type.type_id.id),
                # ("allowed_payable_journal_ids", "in", journal_ids),
            ]
            account_ids = obj_allowed.search(criteria).mapped(
                lambda r: r.allowed_payable_account_ids
            )
            comm_type.allowed_payable_account_ids = account_ids

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
