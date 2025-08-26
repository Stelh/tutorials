from odoo import models, fields, api
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta

GARDEN_SELECTION = [
        ('north', 'North'),
        ('south', 'South'),
        ('east', 'East'),
        ('west', 'West')
    ]

STATE_SELECTION = [
        ('new', 'New'),
        ('offer_received', 'Offer Received'),
        ('offer_accepted', 'Offer Accepted'),
        ('sold', 'Sold'),
        ('canceled', 'Canceled')
    ]

class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Estate Property'
    _order = 'id desc'
    
    name = fields.Char(string="Title", required=True,default="New",copy=False)
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date(copy=False,default=lambda self: fields.Date.today() + timedelta(days=90))
    
    expected_price = fields.Float(required=True)
    @api.constrains('expected_price')
    def _check_expected_price(self):
        if float_compare(self.expected_price, 0, precision_digits=2) == -1:
            raise ValidationError("Expected price must be greater than 0")
    
    selling_price = fields.Float(readonly=True, copy=False)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facade = fields.Integer()
    garage = fields.Boolean()
    
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection(
        selection=GARDEN_SELECTION,
        string="Garden Orientation",
        help="Orientation of the garden"
    )
    @api.onchange('garden')
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = 0
            self.garden_orientation = False
    
    state = fields.Selection(
        selection=STATE_SELECTION,
        string="State",
        help="State of the property",
        default='new'
    )
    active = fields.Boolean(default=True)
    
    property_type_id = fields.Many2one('estate.property.type', string="Property Type")
    property_tag_ids = fields.Many2many('estate.property.tag', string="Tags")
    buyer_id = fields.Many2one('res.partner', string="Buyer",copy=False)
    salesperson_id = fields.Many2one('res.users', string="Salesperson", default=lambda self: self.env.user,index=True)
    offer_ids = fields.One2many('estate.property.offer', 'property_id', string="Offers")
    
    total_area = fields.Float(compute="_compute_total_area")
    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area
    
    best_price = fields.Float(compute="_compute_best_price")
    @api.depends('offer_ids.price')
    def _compute_best_price(self):
        for record in self:
            record.best_price = max(record.offer_ids.mapped('price'), default=0.0)
    
    check_offers = fields.Boolean(compute='_compute_check_offers', store=True)
    @api.depends('offer_ids')
    def _compute_check_offers(self):
        for record in self:
            record.check_offers = len(record.offer_ids) > 0
        if record.check_offers:
            record.state = 'offer_received'
            return
        record.state = 'new'
    
    # Button action
    def action_sold(self):
        if self.state == 'canceled':
            raise UserError("You cannot sell a canceled property")
        self.state = 'sold'
    
    def action_cancel(self):
        if self.state == 'sold':
            raise UserError("You cannot cancel a sold property")
        self.state = 'canceled'
    
    def action_reset(self):
        self.state = 'new'
        tmp = self.expected_price
        # Temporarily set expected_price to 0 to bypass @api.constrains validation during reset
        self.expected_price = 0
        self.selling_price = 0
        self.expected_price = tmp
        self.buyer_id = False
        if self.offer_ids:
            for record in self.offer_ids:
                record.status = False