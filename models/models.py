from odoo import api, fields, models, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError


class RestaurantItem(models.Model):
    _name = 'restaurant.item'
    _description = "Restaurant Item"

    name = fields.Char('Item Name', required=True)
    price = fields.Integer("Item Price", required=True)


class RestaurantMenu(models.Model):
    _name = 'restaurant.menu'
    _description = "Restaurant Menu"

    item_name = fields.Many2one('restaurant.item', required=True)
    item_price = fields.Integer(related='item_name.price', required=True)
    item_quantity = fields.Integer("Quantity", required=True)
    total_price = fields.Integer('Total Price')
    bill_table = fields.Many2one('restaurant.bill')

    @api.onchange('item_name','item_price','item_quantity')
    def _compute_total_price(self):
        if self.item_price and self.item_quantity:
            self.total_price = self.item_price * self.item_quantity

class RestaurantTable(models.Model):
    _name = 'restaurant.tables'
    _description = "Restaurant Table"

    name = fields.Char('Table Name', required=True)
    table_state = fields.Selection([('UnOccupied', 'UnOccupied'), ('Occupied', 'Occupied')],default='UnOccupied', string="State")


class RestaurantBill(models.Model):
    _name = 'restaurant.bill'
    _description = "Restaurant Bill"
    _rec_name = 'table_name_id'

    table_name_id = fields.Many2one('restaurant.tables', required=True)
    state = fields.Selection([('Draft', 'Draft'), ('Dinning', 'Dinning'), ('Billed', 'Billed')], default='Draft')
    total_price = fields.Integer('Total Price')
    gst = fields.Float("GST %", default=12.0)
    menu_item = fields.One2many('restaurant.menu', 'bill_table')
    sub_total = fields.Float('Sub Total')

    def confirm_dinning(self):
        self.state = 'Dinning'
        self.table_name_id.table_state = 'Occupied'

    def confirm_billing(self):
        if self.menu_item:
            total_price = 0
            for price in self.menu_item:
                print(price.total_price)
                total_price += price.total_price
            self.total_price = total_price
            if self.gst and self.total_price:
                amount_after_gst = float(self.total_price)*self.gst/100
                self.sub_total = round(float(self.total_price) + amount_after_gst)
            else:
                raise UserError('GST Not Added')
            self.state = 'Billed'
            self.table_name_id.table_state = 'UnOccupied'
        return {'type': 'ir.actions.report',
                'report_name': 'msy_restaurant.bill_printing',
                'report_type': "qweb-pdf"
                }

    def unlink(self):
        if self.state == 'Billed':
            raise UserError("Cannot Delete Bill in Billed State")
        return super(RestaurantBill, self).unlink()
