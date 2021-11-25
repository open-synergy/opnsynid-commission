# Copyright 2021 PT. Simetri Sinergi Indonesia
# Copyright 2021 OpenSynergy Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Commission",
    "version": "11.0.1.0.0",
    "license": "LGPL-3",
    "category": "Commission",
    "website": "https://simetri-sinergi.id",
    "author": "PT. Simetri Sinergi Indonesia, OpenSynergy Indonesia",
    "depends": [
        "mail",
        "account",
        "ssi_policy_mixin",
        "ssi_multiple_approval_mixin",
        "ssi_sequence_mixin",
        # "ssi_mixin_state_change_history",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/commission_type_views.xml",
        "views/commission_commission_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
