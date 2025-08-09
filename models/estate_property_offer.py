from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError

class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Estate Property Offer'
    
    price = fields.Float(string="Price", required=True)
    status = fields.Selection(string="Status",
                                selection=[('accepted', 'Accepted'), ('refused', 'Refused')],
                                copy=False)

    partner_id = fields.Many2one('res.partner', string="Partner",required=True,ondelete='cascade')
    property_id = fields.Many2one('estate.property', string="Property",required=True,ondelete='cascade')
    
    create_date = fields.Date(string="Offer Date", 
                                default=lambda self: fields.Date.today(),readonly=True)
    validity = fields.Integer(string="Validity (days)",default=7)
    date_deadline = fields.Date(compute="_compute_date_deadline", inverse="_validity_date")

    @api.depends('validity')
    def _compute_date_deadline(self):
        for record in self:
            record.date_deadline = record.create_date + timedelta(days=record.validity)

    def _validity_date(self):
        for record in self:
            record.validity = (record.date_deadline - record.create_date).days
    
    def action_accept(self):
        if self.property_id.selling_price == 0:
            self.status = 'accepted'
            self.property_id.selling_price = self.price
            self.property_id.buyer_id = self.partner_id
            self.property_id.state = 'offer_accepted'
            return True
        else:
            raise UserError("You cannot accept an offer for a sold property")
            return False

    
    def action_refuse(self):
        self.status = 'refused'
        if self.property_id.buyer_id == self.partner_id:
            self.property_id.buyer_id = False
            self.property_id.selling_price = 0
            self.property_id.state = 'new'
            return True
        return False
        