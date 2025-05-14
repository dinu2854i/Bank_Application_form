from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)


class BankApplicationForm(models.Model):
    _name = "bank.application.form"
    _description = "Bank Application Form"
    _inherit = ['mail.thread']
    

     # Fields
    full_name = fields.Char(string="Full Name", required=True)
    pan_number = fields.Char(string="PAN Number", required=True)
    email = fields.Char(string="Email")
    dob = fields.Date(string="Date of Birth", required=True)
    aadhaar_number = fields.Char(string="Aadhaar Number", required=True)
    mobile = fields.Char(string="Mobile", required=True)
    account_type = fields.Selection([
        ('savings', 'Savings'),
        ('current', 'Current'),
    ], string="Account Type", required=True)
    kyc_doc = fields.Binary(string="KYC Document", required=True)  
    kyc_video_call = fields.Boolean(string="KYC Video Call Completed", default=False)
    video_call_link = fields.Char(string="Video Call Link", readonly=True)
    customer_photo = fields.Binary(string="Customer Photo", required=True)
    e_sign_file = fields.Binary(string="E-Signature File", required=True)
    e_sign_filename = fields.Char(string="E-Sign Filename", required=True)
    initial_deposit_amount = fields.Float(string="Initial Deposit Amount", required=True, default=0.00)
    live_photo_verified = fields.Boolean(string="Live Photo Verified", default=False)
    reference = fields.Char(string='Application ID', readonly=True, copy=False, default='New')
    deposit_nature = fields.Selection([
    ('savings', 'Savings'),
    ('current', 'Current'),
    ('recurring', 'Recurring Deposit'),
    ('fixed', 'Fixed Deposit'), 
    ], string="Nature of Deposit", required=True)

    operation_mode = fields.Selection([
        ('single', 'Single'),
        ('joint', 'Joint')
    ], string="Account Operation", required=True)
    terms_accepted = fields.Boolean(string="Terms and Conditions", required=True)
    state = fields.Selection([
    ('draft', 'Draft'),
    ('submitted', 'Submitted'),
    ], string='Status', default='draft', tracking=True, required=True)
    customer_photo = fields.Binary(string="Customer Photo", required=True)
    id_proof = fields.Binary(string="ID Proof", required=True)
    # Nominee Fields
    nominee_name = fields.Char(string="Nominee Name")
    nominee_contact = fields.Char(string="Nominee Contact")
    nominee_relationship = fields.Char(string="Relationship with Nominee")
    nominee_relationship = fields.Selection([
    ('spouse', 'Spouse'),
    ('father', 'Father'),
    ('mother', 'Mother'),
    ('brother', 'Brother'),
    ('sister', 'Sister'),
    ('son', 'Son'),
    ('daughter', 'Daughter'),
    ('other', 'Other'),
    ], string="Relationship with Nominee")

    agreement_confirmed = fields.Boolean(string="I agree to the terms and conditions", required=True)
    # Constraints
    def start_video_kyc(self):
        for record in self:
            try:
                twilio_api_url = 'https://video.twilio.com/v1/Rooms'
                account_sid = 'your_twilio_account_sid'
                auth_token = 'your_twilio_auth_token'

                room_name = f"kyc_call_{record.id}"
                some_data_for_call = {
                    'UniqueName': room_name,
                    'Type': 'peer-to-peer'
                }

                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                }

                response = requests.post(
                    twilio_api_url,
                    data=some_data_for_call,
                    headers=headers,
                    auth=(account_sid, auth_token)
                )

                if response.status_code in [200, 201]:
                    video_call_link = f"https://video.twilio.com/room/{room_name}"
                    record.video_call_link = video_call_link
                    record.message_post(body=f"✅ Video KYC started. Link: <a href='{video_call_link}' target='_blank'>{video_call_link}</a>")
                else:
                    _logger.error(f"Twilio API Error: {response.text}")
                    raise UserError("❌ Failed to start Video KYC. Please check Twilio settings.")

            except Exception as e:
                _logger.exception("Exception during Video KYC")
                raise UserError(f"⚠️ An error occurred: {str(e)}")

    from odoo.exceptions import UserError

    def capture_live_photo(self):
     photo_data = self.env.context.get('photo_data')

     if not photo_data:
        raise UserError("📸 link expaired.")


    @api.model
    def complete_video_kyc(self, record):
     record.kyc_video_call = True
     record.message_post(body="Video KYC successfully completed.")


    @api.model
    def action_complete_kyc(self):
        for record in self:
        
            record.message_post(body="KYC completed successfully via video call.")
    
    # Constraints and other methods...  
    @api.constrains('mobile')
    def _check_mobile_number(self):
        for record in self:
            if not record.mobile or not record.mobile.isdigit() or len(record.mobile) != 10 :
                raise ValidationError("Mobile number must be exactly 10 digits.")
   
   
    @api.constrains('nominee_contact')
    def _check_nominee_contact(self):
     for record in self:
        if record.nominee_contact:
            if not record.nominee_contact.isdigit() or len(record.nominee_contact) != 10:
                raise ValidationError("Nominee contact number must be exactly 10 digits.")

    @api.constrains('email')
    def _check_email_format(self):
        for record in self:
            if record.email:
                email_regex = r"^[a-zA-Z0-9._%+-]+@.+\.com$"
                if not re.match(email_regex, record.email):
                    raise ValidationError("Please enter a valid email address.")
    
    @api.constrains('pan_number')
    def _check_pan_number_format(self):
        for record in self:
            if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', record.pan_number or ''):
                raise ValidationError("PAN must be 10 characters in the format: 5 letters, 4 digits, 1 letter (e.g., ABCDE1234F).")

    @api.constrains('aadhaar_number')
    def _check_aadhaar_number_format(self):
        for record in self:
            if not re.match(r'^\d{12}$', record.aadhaar_number or ''):
                raise ValidationError("Aadhaar must be exactly 12 digits.")

    @api.constrains('initial_deposit_amount')
    def _check_initial_deposit(self):
        for record in self:
            if record.initial_deposit_amount <= 499:
                raise ValidationError("Initial deposit amount must be greater than 500.")

    # Model Methods
    @api.model
    def action_complete_esign(self):
        for record in self:
            signing_service_response = self.external_signing_service(record)
            
            if signing_service_response.get('status') != 'signed':
                raise ValidationError("E-Signature could not be completed. Please try again.")
            record.message_post(body="E-Signature successfully completed.")
            record.signed = True  

    @api.model
    def external_signing_service(self, record):
        response = {
            'status': 'signed',  
            'signature_id': '123abc',  
        }
        return response

    def action_view_summary(self):
     self.ensure_one()
     return {
        'type': 'ir.actions.act_window',
        'name': 'Application Summary',
        'res_model': 'bank.application.form',
        'view_mode': 'form',
        'res_id': self.id,
        'view_id': self.env.ref('digital_bank_form.view_bank_application_summary_form').id,
        'target': 'new', 
        'flags': {'form': {'action_buttons': False}}, 
    }


 
    def action_submit_application(self):
     for rec in self:
        rec.state = 'submitted'
        rec.message_post(body="🚀 Application submitted successfully.")

     return {
        'type': 'ir.actions.act_window',
        'name': '🎉 Submission Successful',
        'view_mode': 'form',
        'res_model': 'bank.application.form',
        'res_id': self.id,
        'view_id': self.env.ref('digital_bank_form.view_submission_popup_form').id,
        'target': 'new',
        'flags': {'form': {'action_buttons': False}}, 
    }


    @api.model
    def action_save(self):
        for record in self:
            record.state = 'draft'  
            record.message_post(body="Application saved in draft state.")
        
        return True  

    @api.model
    def create(self, vals):
        if vals.get('reference', 'New') == 'New':
            vals['reference'] = self.env['ir.sequence'].next_by_code('bank.application.form') or 'New'
        
        return super(BankApplicationForm, self).create(vals)

    @api.constrains('agreement_confirmed')
    def _check_agreement(self):
     for record in self:
        if not record.agreement_confirmed:
            raise ValidationError("You must confirm the agreement before submitting.")

    @api.constrains('agreement_confirmed')
    def _check_terms_accepted(self):
     for record in self:
        if not record.terms_accepted:
            raise ValidationError("You must accept the terms and conditions before submitting.")


    def action_complete_video_kyc(self):
     for record in self:
        if not record.video_call_link:
            raise UserError("Please start the video KYC before marking it as completed.")

        record.kyc_video_call = True
        record.message_post(body="✅ Video KYC completed successfully.")
