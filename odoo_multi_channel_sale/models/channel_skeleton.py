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
# Developed By: PRAKASH KUMAR
#################################################################################
from odoo import fields , models, api, _

class ChannelMappings(models.Model):
	_name="channel.mappings"
	_order = 'need_sync'

	@api.model
	def _needaction_domain_get(self):
		return [('need_sync', '=', 'yes')]

	@api.model
	def _channel_domain_get(self):
		return [('state', '=', 'validate')]

	@api.model
	def eComStoreUsed(self):
		channel_list = []
		channel_list = self.env['multi.channel.sale'].get_channel()
		return channel_list

	name = fields.Char(
		compute='_compute_name'
	)
	channel_id = fields.Many2one(
		comodel_name='multi.channel.sale',
		string='Instance',
		required=True,
		domain=_channel_domain_get
	)
	ecom_store = fields.Selection(
		selection='eComStoreUsed',
		string="Channel",
	)
	store_id =  fields.Char(
		string='Store ID',
	)
	need_sync = fields.Selection(
		selection=(('yes','Yes'),('no','No')),
		string='Update Required',
		default='no',
		required=True
	)
 	# _sql_constraints = [
  #       ('channel_store_store_id_uniq',
  #       	'unique(channel_id, store_id)',
  #       	'Store Object ID must be unique for channel mapping!'),
  #   ]
	def _compute_name(self):
		pass


	@api.model
	def get_need_sync_mapping(self,domain):
	    domain = domain and []
	    map_domain =domain+ [
	        ('need_sync', 'in', ['yes']),
	    ]
	    return self.search(map_domain)
