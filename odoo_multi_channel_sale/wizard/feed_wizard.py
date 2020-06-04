# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
##########################################################################

from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
Type = [
	('product.feed', 'Product'),
	('category.feed', 'Category'),
	('order.feed', 'Order'),
	('partner.feed', 'Partner'),
	('shipping.feed','Shipping')
]
class FeedSyncWizard(models.TransientModel):
	_name='feed.sync.wizard'

	@api.model
	def default_get(self,fields):
		res=super(FeedSyncWizard,self).default_get(fields)
		if not res.get('feed_type'):
		    res.update({'feed_type':self._context.get('active_model')})
		return res
	feed_type = fields.Selection(
        Type,
        string='Feed Type',
        required=True
    )
	@api.multi
	def sync_feed(self):
		self.ensure_one()
		message=''
		context = dict(self._context)
		model  =  self.env[context.get('active_model')]
		active_ids = model.browse(context.get('active_ids'))
		# for recrod in self:
		return active_ids.import_items()
