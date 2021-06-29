from flask import Flask, render_template, request
import os
import dotenv

#Creates flask app.
def create_app():
	app = Flask(__name__)
	dotenv_path = os.path.join(os.path.dirname(__file__), '../.env')

	#Load .env into app.
	dotenv.load_dotenv(dotenv_path)

	return app

app = create_app()

@app.route('/')
def home():
	idp_oidc_url = os.environ.get('IDP_OIDC_URL')
	return render_template('home.html', idp_oidc_url=idp_oidc_url)


@app.route('/login')
def login():
	return render_template('client_login.html')

if __name__ == '__main__':
	app.run(port=5001)