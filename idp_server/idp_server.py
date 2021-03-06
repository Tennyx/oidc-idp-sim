from flask import Flask, request, make_response, redirect, jsonify, render_template
import tasks
import jwt
import time
import random
import string
import cryptography
import os
import base64
import dotenv

#Creates flask app.
def create_app():
	app = Flask(__name__)
	dotenv_path = os.path.join(os.path.dirname(__file__), '../.env')

	#Add fresh keypair to .env.
	tasks.generate_rsa_keypair(dotenv_path)

	#Load .env into app.
	dotenv.load_dotenv(dotenv_path)

	#Update Okta IDP config with ngrok URL.
	tasks.update_okta_idp_settings()
	return app

app = create_app()


####################################################
'''Global variable to store auth code in memory through
the OIDC flow.'''
auth_code = ''


####################################################
'''/authorize endpoint.

Grabs the state generated by Okta, generates an
authorization code, sends both back to the Okta 
org's /oauth2/v1/authorize/callback endpoint via
redirect.'''
@app.route('/authorize')
def authorize():
	global auth_code
	state = request.args['state']
	auth_code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
	redirect_uri = f'{request.args["redirect_uri"]}?code={auth_code}&state={state}'
	return render_template('idp_login.html', redirect_uri=redirect_uri)


####################################################
'''/token endpoint.

Okta makes a form encoded backend call to this endpoint
with the following params: 'code', 'grant_type',
'redirect_uri','client_secret','client_id. After
verifying the auth code is valid by comparing it to the
one stored in memory, check the remaining params for
validity. If all is valid, create the JWT tokens and sign
them with your RSA private key, put them in the response
to Okta.'''
@app.route('/token', methods=['POST'])
def token():
	global auth_code

	#Get hard-coded env variables.
	ngrok_issuer = os.environ.get('NGROK_URL')
	okta_domain_url = os.environ.get('OKTA_DOMAIN_URL')
	idp_test_user = os.environ.get('IDP_TEST_USER')
	idp_client_id = os.environ.get('IDP_CLIENT_ID')
	idp_client_secret = os.environ.get('IDP_CLIENT_SECRET')
	okta_app_client_id = os.environ.get('OKTA_CLIENT_ID')

	#Get the body data passed to /token from Okta.
	okta_req_code = request.form['code']
	okta_req_grant_type = request.form['grant_type']
	okta_req_redirect_uri = request.form['redirect_uri']
	okta_req_client_secret = request.form['client_secret']
	okta_req_client_id = request.form['client_id']
	
	#Compare hard coded values with values passed from Okta.
	if (
		auth_code == okta_req_code and
		okta_req_grant_type == 'authorization_code' and
		okta_req_redirect_uri == f'{okta_domain_url}/oauth2/v1/authorize/callback' and
		okta_req_client_id == idp_client_id and
		okta_req_client_secret == idp_client_secret
	):
		#Create iat and expir times for tokens.
		epoch_time = int(time.time())
		exp_time = int(time.time()) + 3600

		#Get dynamically generated private key from .env.
		private_key = os.environ.get('PRIVATE_KEY')

		'''Create and sign id token. For convenience and
		uniqueness, I made the sub, preferred_username,
		email, given_name and family_name the same value.'''
		id_token = jwt.encode({
			"sub": idp_test_user,
			"aud": okta_app_client_id,
			"iss": ngrok_issuer,
			"iat": epoch_time,
			"exp": exp_time,
			"preferred_username": idp_test_user,
			"email": idp_test_user,
			"given_name": idp_test_user,
			"family_name": idp_test_user
		},
		private_key,
		algorithm='RS256',
		headers={"kid": os.environ.get('IDP_KID')}
		)

		#Create and sign access token.
		access_token = jwt.encode({
			"sub": idp_test_user,
			"aud": okta_app_client_id,
			"iss": ngrok_issuer,
			"iat": epoch_time,
			"exp": exp_time,
		},
		private_key,
		algorithm='RS256',
		headers={"kid": os.environ.get('IDP_KID')}
		)

		#Send response with tokens to Okta.
		return make_response(jsonify({
			"access_token": access_token,
			"token_type": "bearer",
			"expires_in": 7199,
			"id_token": id_token
		}), 200)
	else:
		return make_response(jsonify({
			"error": "Unauthorized.",
		}), 401)


####################################################
'''/keys endpoint.

Keys endpoint returns JSON including the manually
created kid value and the programmatically generated
modulus.'''
@app.route('/keys')
def keys():
	return make_response(jsonify({
		"keys": [
			{
			  "alg": "RS256",
			  "e": "AQAB",
			  "n":  os.environ.get('MODULUS'),
			  "kid": os.environ.get('IDP_KID'),
			  "kty": "RSA",
			  "use": "sig",
			},
		]
	}
	), 200)


####################################################
'''/userinfo endpoint.

For flows where the optional /userinfo is populated in
the Okta config, this endpoint validates the access token
passed by Okta, then returns user profile information.'''
@app.route('/userinfo')
def userinfo():
	'''Checks auth header for Bearer format and extracts
	access token. PyJwt library handles checking format,
	signature and audience claim. If any of these fail,
	returns 401.'''
	try:
		access_token = request.headers.get('Authorization').split('Bearer ')[1]
		decoded_jwt = jwt.decode(access_token, os.environ.get('PUBLIC_KEY'), audience=os.environ.get('OKTA_CLIENT_ID'), algorithms=['RS256'])
	except:
		return make_response(jsonify({
			'error': 'Unauthorized.',
		}), 401)

	#Validates token exp and issuer claims.
	if(
		decoded_jwt['exp'] > int(time.time()) and
		decoded_jwt['iss'] == os.environ.get('NGROK_URL')
	):
		'''For simplicity, and since there is no actual db
		where data is being returned, this just returns the
		user email for all the profile attributes.'''
		idp_test_user = os.environ.get('IDP_TEST_USER')
		return make_response(jsonify({	
			"sub": idp_test_user,		
			"preferred_username": idp_test_user,
			"email": idp_test_user,
			"given_name": idp_test_user,
			"family_name": idp_test_user
		}), 200)
	else:
		return make_response(jsonify({
			'error': 'Unauthorized.',
		}), 401)	

if __name__ == '__main__':
	app.run()