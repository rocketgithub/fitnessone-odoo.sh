# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
import odoo
import base64
from odoo import http, SUPERUSER_ID
import werkzeug
from odoo.http import request
from odoo.addons.web.controllers.main import WebClient, Binary,binary_content
import logging
_logger = logging.getLogger(__name__)
MAPPINGMODEL={
	'product.product':'channel.product.mappings',
	'sale.order':'channel.order.mappings',
	}
MAPPINGFIELD={
	'product.product':'erp_product_id',
	'sale.order':'odoo_order_id',
}

class Channel(http.Controller):
	@http.route(['/channel/update/mapping',],auth="public", type='json')
	def update_mapping(self, **post):
		field =MAPPINGFIELD.get(str(post.get('model')))
		model = MAPPINGMODEL.get(str(post.get('model')))
		if field and model:
			domain = [(field,'=',int(post.get('id')))]
			mappings=request.env[model].sudo().search(domain)
			for mapping in mappings:pass
				#mapping.need_sync='yes'
		return True


	# @http.route(['/web/image',
	# 	'/web/image/<string:xmlid>',
	# 	'/web/image/<string:xmlid>/<string:filename>',
	# 	'/web/image/<string:xmlid>/<int:width>x<int:height>',
	# 	'/web/image/<string:xmlid>/<int:width>x<int:height>/<string:filename>',
	# 	'/web/image/<string:model>/<int:id>/<string:field>',
	# 	'/web/image/<string:model>/<int:id>/<string:field>/<string:filename>',
	# 	'/web/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>',
	# 	'/web/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>/<string:filename>',
	# 	'/web/image/<int:id>',
	# 	'/web/image/<int:id>/<string:filename>',
	# 	'/web/image/<int:id>/<int:width>x<int:height>',
	# 	'/web/image/<int:id>/<int:width>x<int:height>/<string:filename>',
	# 	'/web/image/<int:id>-<string:unique>',
	# 	'/web/image/<int:id>-<string:unique>/<string:filename>',
	# 	'/web/image/<int:id>-<string:unique>/<int:width>x<int:height>',
	# 	'/web/image/<int:id>-<string:unique>/<int:width>x<int:height>/<string:filename>'], type='http', auth="public")
	def core_content_image(self, xmlid=None, model='ir.attachment', id=None, field='datas',
					  filename_field='datas_fname', unique=None, filename=None, mimetype=None,
					  download=None, width=0, height=0, crop=False, access_token=None):
		contenttype = kwargs.get('wk_mime_type') or 'image/jpg'
		status, headers, content = binary_content(
			xmlid=xmlid, model=model, id=id, field=field, unique=unique, filename=filename,
			filename_field=filename_field, download=download, mimetype=mimetype,
			default_mimetype='image/jpg', access_token=access_token)
		if status == 304:
			return werkzeug.wrappers.Response(status=304, headers=headers)
		elif status == 301:
			return werkzeug.utils.redirect(content, code=301)
		elif status != 200 and download:
			return request.not_found()

		height = int(height or 0)
		width = int(width or 0)

		if crop and (width or height):
			content = crop_image(content, type='center', size=(width, height), ratio=(1, 1))

		elif content and (width or height):
			# resize maximum 500*500
			if width > 500:
				width = 500
			if height > 500:
				height = 500
			content = odoo.tools.image_resize_image(base64_source=content, size=(width or None, height or None), encoding='base64', filetype='PNG')
			# resize force jpg as filetype
			headers = Binary().force_contenttype(headers, contenttype='image/jpg')

		if content:
			image_base64 = base64.b64decode(content)
		else:
			image_base64 = Binary().placeholder(image='placeholder.jpg')  # could return (contenttype, content) in master
			headers = Binary().force_contenttype(headers, contenttype='image/jpg')

		headers.append(('Content-Length', len(image_base64)))
		response = request.make_response(image_base64, headers)
		response.status_code = status
		return response

	@http.route([
	'/channel/image.png',
	'/channel/image/<xmlid>.png',
	'/channel/image/<xmlid>/<int:width>x<int:height>.png',
	'/channel/image/<xmlid>/<field>.png',
	'/channel/image/<xmlid>/<field>/<int:width>x<int:height>.png',
	'/channel/image/<model>/<id>/<field>.png',
	'/channel/image/<model>/<id>/<field>/<int:width>x<int:height>.png',
	'/channel/image.jpg',
	'/channel/image/<xmlid>.jpg',
	'/channel/image/<xmlid>/<int:width>x<int:height>.jpg',
	'/channel/image/<xmlid>/<field>.jpg',
	'/channel/image/<xmlid>/<field>/<int:width>x<int:height>.jpg',
	'/channel/image/<model>/<id>/<field>.jpg',
	'/channel/image/<model>/<id>/<field>/<int:width>x<int:height>.jpg'
	], type='http', auth="public", website=False, multilang=False)
	def content_image(self, id=None, max_width=492, max_height=492, **kw):
		if max_width:
			kw['width'] = max_width
		if max_height:
			kw['height'] = max_height
		if id:
			id, _, unique = id.partition('_')
			kw['id'] = int(id)
			if unique:
				kw['unique'] = unique
		kw['wk_mime_type'] = 'image/jpg'
		return self.core_content_image(**kw)
