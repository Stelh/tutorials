from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta

class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Estate Property'
    
    name = fields.Char(string="Title", required=True,default="New",copy=False)
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date(copy=False,default=lambda self: fields.Date.today() + timedelta(days=90))
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True, copy=False)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facade = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_selection = [
        ('north', 'North'),
        ('south', 'South'),
        ('east', 'East'),
        ('west', 'West')
    ]
    garden_orientation = fields.Selection(
        selection=garden_selection,
        string="Garden Orientation",
        help="Orientation of the garden"
    )
    state_selection = [
        ('new', 'New'),
        ('offer_received', 'Offer Received'),
        ('offer_accepted', 'Offer Accepted'),
        ('sold', 'Sold'),
        ('canceled', 'Canceled')
    ]
    state = fields.Selection(
        selection=state_selection,
        string="State",
        help="State of the property"
    )
    active = fields.Boolean(default=True)
    
    property_type_id = fields.Many2one('estate.property.type', string="Property Type")
    property_tag_ids = fields.Many2many('estate.property.tag', string="Tags")
    buyer_id = fields.Many2one('res.partner', string="Buyer",copy=False)
    salesperson_id = fields.Many2one('res.users', string="Salesperson", default=lambda self: self.env.user,index=True)
    offer_ids = fields.One2many('estate.property.offer', 'property_id', string="Offers")
    
    total_area = fields.Float(compute="_compute_total_area")
    best_price = fields.Float(compute="_compute_best_price")
    
    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area
    
    @api.depends('offer_ids.price')
    def _compute_best_price(self):
        for record in self:
            record.best_price = max(record.offer_ids.mapped('price'), default=0.0)
    
    @api.onchange('garden')
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = 0
            self.garden_orientation = False
    
    # Bouton action
    def action_sold(self):
        if self.state != 'canceled':
            self.state = 'sold'
            return True
        else:
            raise UserError("You cannot sell a canceled property")
            return False
    
    def action_cancel(self):
        if self.state != 'sold':
            self.state = 'canceled'
            return True
        else:
            raise UserError("You cannot cancel a sold property")
            return False
    
    def action_reset(self):
        self.state = 'new'
        self.selling_price = 0.0
        self.buyer_id = False
        for record in self.offer_ids:
            record.status = False
        return True