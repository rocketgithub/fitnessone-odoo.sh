# -*- coding: utf-8 -*-
##########################################################################
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
# Developed By: Vikash Mishra
##########################################################################

from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def _action_done(self):
        """ Makes the move done and if all moves are done, it will finish the picking.
        @return:
        """
        context = self.env.context.copy() or {}
        super(StockMove, self)._action_done()
        channel_ids = self.env['multi.channel.sale'].search([]).ids
        todo = [move.id for move in self if move.state == "draft"]
        ids = self
        i=0
        if todo:
            ids = self.action_confirm(todo)
        for data in ids:
            # data = self.browse(id.id)
            erp_product_id = data.product_id.id
            flag = 1  # means there is some origin.
            if (data.origin != False) and data.picking_type_id.code not in ['incoming']:
                # Check if origin is 'Sale' and channel is available,no need to update
                # quantity on this particular channel.
                sale_id = self.env['sale.order'].search([('name', '=', data.origin)])
                if sale_id:
                    channel_id = sale_id.channel_mapping_ids.channel_id
                    def_location = channel_id.location_id.id
                    if channel_id and channel_id.id in channel_ids:
                        channel_ids.remove(channel_id.id)
                    flag = 0 # no need to update quantity on this channel id, update on others channels.
            else:
                flag = 2  # no origin.

            if flag == 1:
                if data.picking_type_id:
                    check_pos = self.env['ir.model'].search([('model', '=', 'pos.order')])
                    if check_pos:
                        pos_order_data = self.env['pos.order'].search(
                            [('name', '=', data.origin)])
                        if pos_order_data:
                            lines = pos_order_data[0].lines
                            for line in lines:
                                get_line_data = self.env['pos.order.line'].search(
                                    [('product_id', '=', erp_product_id), ('id', '=', line.id)])
                                if get_line_data:
                                    data.product_qty = get_line_data[0].qty
            if channel_ids:
                pick_details = {
                    'product_id' :  erp_product_id,
                    'location_dest_id' : data.location_dest_id.id,
                    'product_qty' :  data.product_qty,
                    'channel_ids' :  channel_ids,
                    'source_loc_id' : data.location_id.id,
                }
                self.multichannel_sync_quantity(pick_details)
        return True

    # Extra function to update quantity(s) of product to prestashop`s end.
    @api.multi
    def multichannel_sync_quantity(self, pick_details):
        """ Method to be overriden by the multichannel modules to provide real time stock
        update feature
        """
        # _logger.info("--- sync quantities----------------   %r  ---------------------",[pick_details])
        return True
