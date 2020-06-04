# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

from odoo import fields,api,models 
import logging
_logger = logging.getLogger(__name__)

class ProductImportUpdate(models.TransientModel):
    _name = "product.import.update"

    import_update = fields.Selection(selection=[('import','Import'),('update','Update')],
											   string="Import Operations",
											   default="import")
    date = fields.Datetime("Date", default=lambda self: fields.datetime.now())
    one_time_import = fields.Boolean(string='First Time Import',
                                    help="If you have large no. of products on your woocommerce  site then enable this It will import product page by page",
                                    default = False)

    @api.multi
    def process(self):
        if 'active_id' in self._context:
            channel = self.env['multi.channel.sale'].browse(self._context['active_id'])
            if channel:
                if self.import_update == 'import':
                    if self.one_time_import:
                        message = channel.import_all_woocommerce_products()
                    else:
                        channel.import_product_date = self.date
                        message = channel.import_woocommerce_products()
                else:
                    # channel.update_product_date = self.date
                    message = channel.update_woocommerce_products()
                return message
            raise Warning("No Channel Id")

class OrderImportUpdate(models.TransientModel):
    _name = "order.import.update"

    import_update = fields.Selection(selection=[('import','Import'),('update','Update')],
											   string="Import Operations",
											   default="import")
    date = fields.Datetime("Date" , default=lambda self: fields.datetime.now())
    one_time_import = fields.Boolean(string='First Time Import',help="If you have large no. of orders on your woocommerce  site then enable this It will import orders page by page",default = False)
    @api.multi
    def process(self):
        if 'active_id' in self._context:
            channel = self.env['multi.channel.sale'].browse(self._context['active_id'])
            if channel:
                if self.import_update == 'import':
                    if self.one_time_import:
                        message = channel.import_all_woocommerce_orders()
                    else:
                        channel.import_order_date = self.date
                        message = channel.import_woocommerce_orders()
                else:
                    # channel.update_order_date = self.date
                    message = channel.update_woocommerce_orders()
                return message
            raise Warning("No Channel Id")

class ProductExportUpdate(models.TransientModel):
    _name = "product.export.update"

    import_update = fields.Selection(selection=[('export','Export'),('update','Update')],
											   string="Export Operations",
											   default="export")

    @api.multi
    def process(self):
        if 'active_id' in self._context:
            channel = self.env['multi.channel.sale'].browse(self._context['active_id'])
            if channel:
                if self.import_update == 'export':
                    message = channel.export_woocommerce_product()
                else:
                    message = channel.export_update_woocommerce_product()
                return message
            raise Warning("No Channel Id")

class PartnerImportUpdate(models.TransientModel):
    _name = "partner.import.update"

    import_update = fields.Selection(selection=[('import','Import'),('update','Update')],
											   string="Import Operations",
											   default="import")
    date = fields.Datetime("Date", default=lambda self: fields.datetime.now())
    one_time_import = fields.Boolean(string='First Time Import',help="If you have large no. of customers on your woocommerce  site then enable this It will import product page by page",default = False)

    @api.multi
    def process(self):
        if 'active_id' in self._context:
            channel = self.env['multi.channel.sale'].browse(self._context['active_id'])
            if channel:
                if self.import_update == 'import':
                    if self.one_time_import:
                        message = channel.import_all_woocommerce_customers()
                    else:
                        channel.import_customer_date = self.date
                        message = channel.import_woocommerce_customers()
                else:
                    channel.update_customer_date = self.date
                    message = channel.update_woocommerce_customers()
                return message
            raise Warning("No Channel Id")

#-----------------------------------------------------------------------------------------------
class CategoryImportUpdate(models.TransientModel):
    _name = "category.import.update"

    import_update = fields.Selection(selection=[('import','Import'),('update','Update')],
											   string="Import Operations",
											   default="import")

    @api.multi
    def process(self):
        if 'active_id' in self._context:
            channel = self.env['multi.channel.sale'].browse(self._context['active_id'])
            if channel:
                if self.import_update == 'import':
                    message = channel.import_woocommerce_categories()
                else:
                    message = channel.update_woocommerce_categories()
                return message
            raise Warning("No Channel Id")

#-----------------------------------------------------------------------------------------------
class CategoryExportUpdate(models.TransientModel):
    _name = "category.export.update"

    import_update = fields.Selection(selection=[('export','Export'),('update','Update')],
											   string="Export Operations",
											   default="export")

    @api.multi
    def process(self):
        message = ''
        if 'active_id' in self._context:
            channel = self.env['multi.channel.sale'].browse(self._context['active_id'])
            if channel:
                if self.import_update == 'export':
                    count = channel.export_woocommerce_categories(0)
                    message += str(count)+" Categories have been exported"
                    return channel.display_message(message)
                else:
                    message = channel.export_update_woocommerce_categories()
                    return message
            raise Warning("No Channel Id")