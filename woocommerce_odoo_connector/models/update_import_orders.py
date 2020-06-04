#!/usr/bin/env python
# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

from odoo import api,fields,models
from odoo.tools.translate import _
from datetime import datetime,timedelta
from odoo.addons.odoo_multi_channel_sale.tools import extract_list as EL
from odoo.exceptions import UserError
import logging
_logger	 = logging.getLogger(__name__)
try:
	from woocommerce import API
except ImportError:
	_logger.info('**Please Install Woocommerce Python Api=>(cmd: pip3 install woocommerce)')
class MultiChannelSale(models.Model):
	_inherit = "multi.channel.sale"

	@api.multi
	def update_woocommerce_orders(self, woocommerce=False):
		update_rec = []
		count = 0
		if not woocommerce:
			woocommerce = self.get_woocommerce_connection()
		order_feed_data = self.env['order.feed']
		records = self.env['channel.order.mappings'].search([('channel_id.id','=',self.id)])
		id_string = []
		idstr =''
		i=0
		for record in records:
			idstr+=str(record.store_order_id)+','
			i +=1
			if i==10:
				id_string.append(idstr)
				i=0
				idstr=''
		if idstr not in id_string:
			id_string.append(idstr)
		for id_str in id_string:
			try:
				order_data = woocommerce.get('orders?include='+id_str).json()
			except Exception as e:
				raise UserError(_("Error : "+str(e)))
			if 'message' in order_data:
				raise UserError(_("Error : "+str(order_data['message'])))
			else :
				for order in order_data:
					update_record = self.env['order.feed'].search([('store_id','=',order['id']),('channel_id.id','=',self.id)])
					if update_record and update_record.order_state != order['status']:
						count += 1
						update_record.state = 'update'
						order_dict = {
									'order_state': order['status']
						}
						update_record.write(order_dict)
						update_rec.append(update_record)
		feed_res = dict(create_ids=[],update_ids=update_rec)
		self.env['channel.operation'].post_feed_import_process(self,feed_res)
		self.update_order_date = str(datetime.now().date())
		message = str(count)+" Order(s) Updated!  "
		return self.display_message(message)
