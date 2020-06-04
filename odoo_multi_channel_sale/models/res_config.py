# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2017-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
# Developed By: Jahangir Ahmad

from odoo import api, fields, models
import logging


class MultiChannelSaleConfig(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'multi.channel.sale.config'

    avoid_duplicity = fields.Boolean(
        string="Avoid Duplicity (Default Code)",
        help="Check this if you want to avoid the duplicity of the imported products. In this case the product with same default code/sku will not create again and again.")
    avoid_duplicity_using = fields.Selection(
        [('default_code', 'Default Code/SKU'),
        ('barcode', 'Barcode/UPC/EAN/ISBN'), ('both', 'Both')],
        string="Avoid Duplicity Using",
        default='both',
        help="In Both option the the uniquenes will be wither on sku/Default or UPC/EAN/Barcode usign OR operator and it should be always be given high priority")

    @api.multi
    def set_values(self):
        super(MultiChannelSaleConfig, self).set_values()
        IrDefault = self.env['ir.default'].sudo()
        IrDefault.set('multi.channel.sale.config', 'avoid_duplicity',
        self.avoid_duplicity)
        IrDefault.set('multi.channel.sale.config', 'avoid_duplicity_using',
        self.avoid_duplicity_using)
        return True
    @api.model
    def get_values(self):
        res = super(MultiChannelSaleConfig, self).get_values()
        IrDefault = self.env['ir.default'].sudo()
        res.update(
            {
            'avoid_duplicity':IrDefault.get('multi.channel.sale.config', 'avoid_duplicity'),
            'avoid_duplicity_using':IrDefault.get('multi.channel.sale.config', 'avoid_duplicity_using' or 'both')
            }
        )
        return res
