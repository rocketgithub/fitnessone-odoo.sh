# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
import base64
import urllib
import os
import logging
logger = logging.getLogger(__name__)
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ProductImage(models.Model):
    _inherit = ["product.image"]

    @api.model
    def create(self, vals):
        if vals.get('name', False) and not vals.get('extention', False):
            vals['name'], vals['extention'] = os.path.splitext(vals['name'])
        return super(ProductImage, self).create(vals)

    @api.multi
    @api.depends('file')
    def oe_get_image(self):
        result = {}
        for each in self:result[each.id] = each.with_context(dict(self._context)).get_image()
        return result


    @api.multi
    def oe_set_image(self, _id, value, arg):
        media_repo = self.env['multi.channel.sale'].get_media_repo()
        if media_repo:
            image = self.browse(_id)
            sku_path = image.wk_get_image_sku_path()
            if sku_path and self._wk_ensure_file_dir(sku_path):
                return self.wk_save_file(sku_path , img_name, value)
        return image.write({'file_db_store' : value})



    @staticmethod
    def _wk_ensure_file_dir(self, img_path):
        try:
            if not os.path.isdir(img_path):os.makedirs(image_filestore)
        except Exception as e:
            raise UserError(_('The image filestore can not be created, %s'%e))
        return True

    @staticmethod
    def _wk_ensure_file(self, img_path):
        try:
            if not os.path.isdir(img_path):os.makedirs(image_filestore)
        except Exception as e:
            raise UserError(_('The image filestore can not be created, %s'%e))
        return True

    @staticmethod
    def wk_get_image(self,img_path):
        data = None
        try:
            fdata = open(img_path, 'rb')
            data = base64.encodestring(fdata.read())
            fdata.close()
        except Exception as e:
            pass
        return dict(
            data=data
        )

    @staticmethod
    def wk_save_file(self, path, filename, b64_file):
        try:
            img_file = open( os.path.join(path, filename), 'w')
            img_file.write(base64.b64encode(b64_file))
        finally:
            img_file.close()
        return True

    @staticmethod
    def wk_get_image_sku_path(self,img_name,product_id):
        media_repo =self.media_repo
        if media_repo:
            # img_name = '%s%s'%(self.name, self.img_extention)
            sku_path =os.path.join(media_repo, product_id.default_code)
            return sku_path


    # @api.one
    # def get_image(self):
    #     img_data = None
    #     if self.url:
    #         (filename, header) = urllib.urlretrieve( self.url)
    #         img_data = self.wk_get_image(filename).get('data')
    #     else:
    #         sku_path = self.wk_get_image_sku_path()
    #         if sku_path and os.path.exists(full_path):
    #             img_data = self.wk_get_image(full_path).get('data')
    #         else:
    #             img_data = self.file_db_store
    #     return img_data
    extention = fields.Char(
        string='file extention'
    )
    url = fields.Char(
        string='File Location',
    )
    file_db_store = fields.Binary(
        string='Image stored in database'
    )
    file = fields.Binary(
        compute='oe_get_image',
        fnct_inv=oe_set_image,
        method=True,
        filters='*.png,*.jpg,*.gif'
    )
