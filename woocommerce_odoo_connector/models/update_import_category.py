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
import re
remove_tag = re.compile(r'<[^>]+>')
_logger	 = logging.getLogger(__name__)
try:
	from woocommerce import API
except ImportError:
	_logger.info('**Please Install Woocommerce Python Api=>(cmd: pip3 install woocommerce)')
class MultiChannelSale(models.Model):
	_inherit = "multi.channel.sale"

	@api.multi
	def update_woocommerce_categories(self):
		update_rec = []
		create_rec = []
		count = 0
		woocommerce = self.get_woocommerce_connection()
		category_feed_data = self.env['category.feed']
		records = self.env['channel.category.mappings'].search([('channel_id.id','=',self.id)])
		i=0
		id_string = []
		idstr = ''
		for record in records:
			idstr+=str(record.store_category_id)+','
			i +=1
			if i==10:
				id_string.append(idstr)
				i=0
				idstr=''
		if idstr not in id_string:
			id_string.append(idstr)
		for id_str in id_string:
			try:
				category_data = woocommerce.get('products/categories?include='+id_str).json()
			except Exception as e:
				raise UserError(_("Error : "+str(e)))
			if 'errors' in category_data:
				raise UserError(_("Error : "+str(category_data['errors'][0]['message'])))
			else :
				for category in category_data:
					update_record = category_feed_data.search([('store_id','=',category['id']),('channel_id.id','=',self.id)])
					if update_record:
						count += 1
						update_record.state = 'update'
						category_dict = {
									'name'		:category['name'],
									'parent_id'	:category['parent'] or '',
						}
						update_record.write(category_dict)
						update_rec.append(update_record)
					else:
						count = count+1
						category_dict = {
										'name'		:category['name'],
										'parent_id'	:category['parent'] or '',
										'store_id'	:category['id'],
										'channel_id':self.id,
						}
						category_rec = self.env['category.feed'].create(category_dict)
						# category_rec.state = 'update'
						self._cr.commit()
						update_rec.append(category_rec)
		feed_res = dict(create_ids=create_rec,update_ids=update_rec)
		self.env['channel.operation'].post_feed_import_process(self, feed_res)
		message = str(count)+" Categories Updated!  "
		return self.display_message(message)
