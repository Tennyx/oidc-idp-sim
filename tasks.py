import requests
import json
import os
import codecs
import dotenv
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

####################################################
'''If you generate a new ngrok URL and need to update
the Okta IDP or you want to toggle the userinfo flow
on/off (true/false), do so in the .env file. When you
run python app.py, this method will run to ensure your
IDP settings update to match local.'''
def update_okta_idp_settings():
	#Pull in relevant env vars
	ngrok_issuer = os.environ.get('NGROK_URL')
	okta_api_key = os.environ.get('OKTA_API_KEY')
	okta_idp_id = os.environ.get('OKTA_IDP_ID')
	okta_domain_url = os.environ.get('OKTA_DOMAIN_URL')
	userinfo_flow = os.environ.get('USERINFO_FLOW').lower()

	'''Formulate IDP api endpoint to check current config
	against the local config.''' 
	url = f'{okta_domain_url}/api/v1/idps/{okta_idp_id}'

	payload={}
	headers = {
		'Authorization': f'SSWS {okta_api_key}',
		'Content-Type': 'application/json',
		'Accept': 'application/json'
	}

	response = requests.request("GET", url, headers=headers, data=payload)
	idp_config = response.json()
	idp_endpoint_config = idp_config['protocol']['endpoints']
	updated_endpoint_config =  {
			'authorization': {
				'url': f'{ngrok_issuer}/authorize',
				"binding": "HTTP-REDIRECT"
			},
			'token': {
				'url': f'{ngrok_issuer}/token',
				'binding': 'HTTP-POST'
			},
			'jwks': {
				'url': f'{ngrok_issuer}/keys',
				'binding': 'HTTP-REDIRECT'
			}
		}

	if userinfo_flow == 'true':
		updated_endpoint_config['userInfo'] = {'url': f'{ngrok_issuer}/userinfo', 'binding': 'HTTP-REDIRECT'}

	#Update Okta IDP endpoints if change detected.
	if idp_endpoint_config == updated_endpoint_config:
		print('\nOkta IDP settings up-to-date.')
	else:
		idp_config['protocol']['endpoints'] = updated_endpoint_config
		idp_config['protocol']['issuer']['url'] = ngrok_issuer
		updated_response = requests.request("PUT", url, headers=headers, data=json.dumps(idp_config))
		if updated_response.status_code == 200:
			print(f'\nOkta IDP endpoints updated to match ngrok URL {ngrok_issuer} from .env file.')
		else:
			print(f'\nError code {updated_response.status_code} with updating IDP URLS via API. Update manually.')


####################################################
'''Function to generate rsa key pair used to sign
the token signature'''
def generate_rsa_keypair(env_file):
	# generate private/public key pair
	key = rsa.generate_private_key(backend=default_backend(), public_exponent=65537, \
		key_size=2048)

	# get public key in OpenSSH format
	public_key = key.public_key().public_bytes(serialization.Encoding.OpenSSH, \
		serialization.PublicFormat.OpenSSH)

	# get private key in PEM container format
	pem = key.private_bytes(encoding=serialization.Encoding.PEM,
		format=serialization.PrivateFormat.TraditionalOpenSSL,
		encryption_algorithm=serialization.NoEncryption())

	# decode to printable strings
	private_key_str = pem.decode('utf-8')
	public_key_str = public_key.decode('utf-8')

	modulus = codecs.encode(codecs.decode(hex(key.public_key().public_numbers().n)[2:], 'hex'), 'base64').decode()

	# Write changes to .env file.
	dotenv.set_key(env_file, 'PRIVATE_KEY', private_key_str)
	dotenv.set_key(env_file, 'PUBLIC_KEY', public_key_str)
	dotenv.set_key(env_file, 'MODULUS', modulus)

	print('\nKeys generated and added to .env file.\n')