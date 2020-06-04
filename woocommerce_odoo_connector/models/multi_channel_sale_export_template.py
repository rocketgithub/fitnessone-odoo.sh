# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

from odoo import api,models,fields
import logging
_logger = logging.getLogger(__name__)

class ExportTemplates(models.TransientModel):
    _inherit = 'export.templates'

    @api.multi
    def submit(self):
        message=''
        if self.operation == 'export':
            message = self.channel_id.action_export_woocommerce_products()
        else:
            message = self.channel_id.action_update_woocommerce_products()
        return message
