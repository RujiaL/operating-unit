# Copyright 2016-19 Eficent Business and IT Consulting Services S.L.
# Copyright 2016-19 Serpent Consulting Services Pvt. Ltd.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import email_split


class HrExpenseExpense(models.Model):

    _inherit = "hr.expense"

    operating_unit_id = fields.Many2one(
        "operating.unit",
        "Operating Unit",
        default=lambda self: self.env["res.users"].operating_unit_default_get(
            self._uid
        ),
    )

    @api.constrains("operating_unit_id", "company_id")
    def _check_company_operating_unit(self):
        for rec in self:
            if (
                rec.company_id
                and rec.operating_unit_id
                and rec.company_id != rec.operating_unit_id.company_id
            ):
                raise ValidationError(
                    _(
                        "Configuration error. The Company in "
                        "the Expense and in the Operating "
                        "Unit must be the same."
                    )
                )

    @api.constrains("operating_unit_id", "sheet_id")
    def _check_expense_operating_unit(self):
        for rec in self:
            if (
                rec.sheet_id
                and rec.sheet_id.operating_unit_id
                and rec.operating_unit_id
                and rec.sheet_id.operating_unit_id != rec.operating_unit_id
            ):
                raise ValidationError(
                    _(
                        "Configuration error. The Operating "
                        "Unit in the Expense sheet and in the "
                        "Expense must be the same."
                    )
                )

    def action_submit_expenses(self):
        res = super(HrExpenseExpense, self).action_submit_expenses()
        if len(self.mapped("operating_unit_id")) != 1 or any(
            not expense.operating_unit_id for expense in self
        ):
            raise ValidationError(
                _(
                    "You cannot submit the Expenses having "
                    "different Operating Units or with "
                    "no Operating Unit"
                )
            )
        if res.get("context"):
            res.get("context").update(
                {"default_operating_unit_id": self[0].operating_unit_id.id}
            )
        return res

    def _get_account_move_line_values(self):
        res = super(HrExpenseExpense, self)._get_account_move_line_values()
        for expense in self:
            res[expense.id][0].update({"operating_unit_id": expense.operating_unit_id.id})
            res[expense.id][1].update({"operating_unit_id": expense.operating_unit_id.id})
        return res

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """
        Temporary workaround to expenses selecting wrong company.
        Remove when resolved upstream
        :param msg_dict:
        :param custom_values:
        :return:
        """
        email_address = email_split(msg_dict.get("email_from", False))[0]
        employee = self.env["hr.employee"].sudo().search(
            [
                "|",
                ("work_email", "ilike", email_address),
                ("user_id.email", "ilike", email_address),
            ],
            limit=1,
        )
        if not employee:
            raise ValidationError(
                _("Expenses must come from an employee registered as HR Employee")
            )
        company = employee.company_id
        if hasattr(company, "intercompany_user_id"):
            uid = company.intercompany_user_id.id
        else:
            uid = self._uid
        new_self = self.sudo(uid).with_context(force_company=company.id)
        return super(HrExpenseExpense, new_self).message_new(
            msg_dict, custom_values=custom_values
        )


class HrExpenseSheet(models.Model):

    _inherit = "hr.expense.sheet"

    operating_unit_id = fields.Many2one(
        "operating.unit",
        "Operating Unit",
        default=lambda self: self.env["res.users"].operating_unit_default_get(
            self._uid
        ),
    )

    @api.constrains("operating_unit_id", "company_id")
    def _check_company_operating_unit(self):
        for rec in self:
            if (
                rec.company_id
                and rec.operating_unit_id
                and rec.company_id != rec.operating_unit_id.company_id
            ):
                raise ValidationError(
                    _(
                        """Configuration error. The company in
                the Expense and in the Operating Unit must be the same"""
                    )
                )
