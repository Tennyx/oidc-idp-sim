# OIDC External IDP Simulator (Okta as SP)
Custom Identity Provider simulator server made in flask. If you have a custom IDP that you want to integrate with an Okta org, or simply want to know more about what goes on under the hood in an Okta external IDP flow, this repo is for you.

### What you'll need:
- [virtualenv](https://docs.python.org/3/library/venv.html)
- [ngrok](https://ngrok.com/)
- [flask](https://flask.palletsprojects.com/en/1.1.x/)
- [Okta org (free)](https://developer.okta.com/signup/)


## Setup

1. After cloning the repo, `cd` into the folder and create a new virtual environment:

```sh
virtualenv env
```

Then activate it

```sh
source env/bin/activate
```
>(To know your virtual environment is activated, you should see `(env)` at the start of your terminal line.)

2. Install the necessary Python packages with `pip install -r requirements.txt`.

3. In the root folder, create a `.env` file. This is where you'll store all the relevant environment variables.

4. Copy and paste the following into that `.env` file:

```sh
USERINFO_FLOW=false
OKTA_API_KEY=
OKTA_DOMAIN_URL=
OKTA_CLIENT_ID=
IDP_CLIENT_ID=
IDP_CLIENT_SECRET=
IDP_KID=
IDP_TEST_USER=
OKTA_IDP_ID=
IDP_OIDC_URL=
NGROK_URL=
PRIVATE_KEY=
PUBLIC_KEY=
MODULUS=
```
> We will hop back and forth to this `env` file and populate it between development and Okta UI steps. This may seem a bit overwhelming with all the env vars, but some of these will be filled out automatically and others will save you lots of time down the road!

5. If you don't own/have not yet created an [Okta org](https://developer.okta.com/signup/), do so now. 

6. We can start by populating the following vars:

    - `USERINFO_FLOW` - As you can see, this is the only pre-populated field. Okta has two OIDC flows when interacting with an external IDP - a flow involving an optional `/userinfo` endpoint, and a flow without it. More on this later, but for now leave it as `false`.

    - `OKTA_API_KEY` - An Okta API key is NOT needed for the authentication flow. If you are familiar with Okta, this token is mainly used for Okta API management interactions. So why do we need it here? We don't...but unless you're a fan of having to constantly update your Okta identity provider every time you generate a new ngrok link, there is a task in this repo that refreshes your Okta IDP links to match your existing ngrok URL. If you do not have a valid API key saved somewhere from before, create a new one in your Okta org at: **Security** -> **API**. Tab over to **Tokens** and **Create Token**. Paste the value into this env var - and never ever ever let anyone else see it!
    - `OKTA_DOMAIN_URL` - The Okta domain URL for your org.

7. Time to create an app in your Okta org which a user will be accessing. The end game of this repo is to have a user with tokens granted from Okta. We will eventually be running the OIDC IDP server on port 5000 and our client application on port 5001.
    - In your Okta dashboard, go to **Applications** -> **Applications** and click **Add Application**. On the next page, click **Create New App**. Select **Single Page App (SPA)** as your platform. Click **Create**.
    - Name the application whatever you want, add http://localhost:5001/login to the **Login Redirect URIs**, check the Implicit Grant Type and **Save**.
    
    ![SPA_CREATE_1](https://i.imgur.com/WwCld2b.png)
    
    >**NOTE:** In a live setting, you never want to use Implicit flow. It's convenient for testing purposes, but not a secure OIDC flow.
    - With this app created, copy the **Client ID** and return to your .env file and paste it into `OKTA_CLIENT_ID`.
    
8. Next we are going to create some values for the IDP simulator. These values can be anything you want for testing purposes. They will be important/necessary when setting up an external IDP configuration in Okta.
    - `IDP_CLIENT_ID` - Any value you want, typically a string of letters/numbers.
    - `IDP_CLIENT_SECRET`- Any value you want, typically a string of letters/numbers.
    - `IDP_KID` - Any value you want, typically a string of letters/numbers.
    - `IDP_TEST_USER` - A test user that will be 'logging in' to the IDP simulator. Must be in email format to integrate with our eventual Okta external IDP config.
    
9. Now it's finally time to connect the custom IDP sim with your Okta org by creating an external identity provider. In Okta, go to **Security** -> **Identity Providers**, click **Add Identity Provider** and **Add OpenID Connect IdP**.

10. Populate the **Client ID** and **Client Secret** fields with the `IDP_CLIENT_ID` and `IDP_CLIENT_SECRET` from your `.env` file. Fill in the various endpoint fields with a placeholder value - as these will be updated with your ngrok URL once your IDP sim server is started:

    ![IDP_CREATE_1](https://i.imgur.com/WKZYc4l.png)
    
11. You should now see your newly created Identity Provider. Twirl the arrow down on the left side of the IDP config:

    ![IDP_CREATE_2](https://i.imgur.com/bJN33fC.png)
    
    - Copy the **IdP ID** and paste it into your `.env` file for the `OKTA_IDP_ID`  value.
    - As for the **Authorize URL**, you can see Okta has a bunch of placeholder values for customizing this URL. Here's how we will fill these values out before pasting to our `.env`:
        - `{client_id}` - Paste the value from your `.env` variable `OKTA_CLIENT_ID`.
        - `{responseType}` - `id_token`. This means that at the end of the flow, Okta will return a "fat token" with user profile information using the implicit flow.
        - `{responseMode}` - `fragment`. The token mentioned above will appear as a "fragment" after a hash in your URL at our client application endpoint of http://localhost:5001/login.
        - `{scopes}` - `openid profile email`.
        - `{redirectUri}` - `http://localhost:5001/login`. Redirect to our client application.
        - `{state}` - For this testing purpose, it can be whatever you want.
        - `{nonce}` - For this testing purpose, it can be whatever you want.
    
    Once this URL is formed, paste it into `IDP_OIDC_URL` in you `.env` file.

12. Since we are creating our IDP simulator on a local server, we will use `ngrok` to route web traffic to `localhost:5000` (the default port for flask) and vice-versa. It's finally time to generate this URL!
    - In the terminal, type `./ngrok http 5000`. This will fire up ngrok and create a couple URLs that route to your `localhost:5000` address. Copy the link starting with `https` and paste it into your `NGROK_URL` environment variable in `.env`.
13. Your `.env` file should now be fully populated with the exception of `PRIVATE_KEY`, `PUBLIC_KEY`, and `MODULUS`. These will be auto-generated when you...

## Run the Servers 

FINALLY! After all that setup it's finally time to run your OIDC IDP simulator and client app. Navigate back to the terminal (make sure you still see the `(env)` at the beginning of your terminal line, indicating you are still in the Python virtual environment). 


### Run OIDC Server

Let's start with the OIDC IDP server. Run the command `cd idp_server && python idp_server.py`. This fires up your OIDC server on port 5000.

- Two tasks run everytime you initiate this server:

    1. Via the Okta API, IDP URLs are automatically generated and refreshed in your org based off of your `NGROK_URL` value in the `.env`. This is why we only used placeholders before when setting that Okta configuration up. Also, this task will check the value of `USERINFO_FLOW`. When `USERINFO_FLOW` is `false`, this task will ensure the optional **Userinfo endpoint** is empty in your Okta IDP config. When `true`, the task generates a `{NGROK_URL}/userinfo` endpoint in that field.
    
    2. An RSA keypair is generated and those final three environment variables `PRIVATE_KEY`, `PUBLIC_KEY`, and `MODULUS` are autopopulated. This is necessary for the signing of JWT tokens sent to Okta, and for Okta to verify the token signatures from the flask server's `/keys` endpoint. It seemed like dynamically generating new keypairs was preferable to hardcoding values into the app or asking the developer to create their own for a test environment.
    
    
- A Successful server boot will look like this in the terminal:

```sh
Okta IDP endpoints updated to match ngrok URL {NGROK_URL} .env file.

Keys generated and added to .env file.

 * Serving Flask app "app" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
 ```
 
 ### Run Client Application
 
 - Back in terminal, open a new tab with `cmd + t`. Run `cd ..` to jump back to the root of the project. Fire up another virtual environment with `source env/bin/activate`, then type the command `cd client && python client.py`. This spins up your test client application on port 5001.
 
 ## Test it Out!
 - In a browser, navigate to `http://localhost:5001`. You will see our client app running with a link to **Login with External IDP Simulator**. Click it.
 
 ![FLOW_1](https://i.imgur.com/pkeMsir.png)
 
- Next you will be redirected to the IDP's /authorize endpoint where a fake login screen exists. This just exists as an interstitial example and it doesn't matter what (if any) credentials you enter. **Click Login with IDP**

 ![FLOW_1](https://i.imgur.com/wqoCihB.png)
 
- Now an OIDC flow takes behind the scenes between Okta and the IDP, eventually resulting in a redirection to your client app with an ID token granted.

 ## Under the Hood

So you have this setup, hopefully you are successfully receiving a token. But what is going on in this flow? Thanks to `ngrok` and the browser network tab, we can nicely follow this whole process through requests and responses. Navigate to `http://localhost:4040` to see these calls in action. There are also notes in the `idp_server.py` file explaining what is taking place at each endpoint.
  
- When you click **Login with External IDP Simulator** at `http://localhost:5001`, you are redirecting to the `IDP_OIDC_URL` we created earlier in our `.env` file.

```
https://{OKTA_DOMAIN_URL}/oauth2/v1/authorize?
                        idp={OKTA_IDP_ID}
                        client_id={OKTA_CLIENT_ID}&
                        response_type=id_token&
                        response_mode=fragment&
                        scope=openid+email&
                        redirect_uri=http://localhost:5001/login&
                        state=state&
                        nonce=nonce
```
It is almost identical to an OIDC flow with your Okta org as IDP. The big difference is the `idp={OKTA_IDP_ID}` query parameter. This tells Okta to initiate an OIDC flow with the external identity provider that you configured. If the interaction with the external IDP results in valid ID (and sometimes access) tokens being sent to Okta, Okta will then grant tokens to the redirect_uri listed above - allowing for SSO into your application.

- Let's take a look at the request to the IDP sim from Okta:

 ![REQ_1](https://i.imgur.com/oI5J4zU.png)
 
 Okta creates an OIDC GET request with a random `state` value to the `/authorize` endpoint configured in your Identity Provider back in the Okta UI. You can see this endpoint in the `app.py` file of the server how this request is handled by the IDP. It's at this step that a real IDP would prompt the user for credentials before continuing on. For testing purposes we pretend a valid user has submitted credentials, then we generate an authorization code and send it to the Okta callback URI at `{okta_domain_url}/oauth2/v1/authorize/callback` along with the `state` value Okta included in the initial call.
 
- At the callback URL, Okta continues the OIDC flow by checking the state param we sent, pulling the authorization code from the URL and sending a backend request to our `/token` endpoint. As you can see, this /token request contains five parameters in the body:

 - `client_id` - (Your `IDP_CLIENT_ID`)
 - `client_secret` - (Your `IDP_CLIENT_SECRET`)
 - `code` - (The authorization code you generated and sent to `{okta_domain_url}/oauth2/v1/authorize/callback`) 
 - `grant_type` - (Will be `authorization_code`)
 - `redirect_uri` - (Once again the `{okta_domain_url}/oauth2/v1/authorize/callback` URL.)

 ![REQ_2](https://i.imgur.com/lPnzaQu.png)
 
- At the `/token` endpoint in `app.py`, we check all these values to ensure what Okta is sending matches our `.env` values. If everything checks out, we create RS256-signed JWT ID and access tokens to send in our response. In these tokens we inject the `IDP_KID` value we created earlier into the token headers. This value will help Okta to find the public key for JWT validation at the eventual `/keys` endpoint.

- And finally that brings us to the `/keys` endpoint! Okta has received our tokens, but it still can't validate them completely without checking our token signature. To do this, Okta reached out to our `/keys` endpoint, which contains our `IDP_KID` value (from `kid`) to help Okta identify our public key. Okta then uses our `MODULUS` (residing in the `n` parameter) to check the token signature which was signed using our `PRIVATE_KEY`.

 ![REQ_3](https://i.imgur.com/ABiIkwE.png)
 
 This is good enough for Okta! After all these steps, Okta will finally grant its own ID token to the user accessing our client app at `http://localhost:5001/login`.

 ## The Userinfo Flow

One last thing to go over: In the example above, our `.env` `USERINFO_FLOW` value is false. As mentioned before, that means there is no `/userinfo` endpoint populating our external IDP configured in Okta. However - if an endpoint exists in that optional field, the flow looks slightly different. 

- Run `ctrl+c` on your flask OIDC IDP server to cancel it.
- In `.env`, change the `USERINFO_FLOW` value to `true`.
- Back in terminal, run `python idp_server.py` to run the server again. You should see a message `Okta IDP endpoints updated...` as the `/userinfo` endpoint in your IDP config should now be populated. IF this field is populated, Okta will not get user information from the ID token returned, but rather it will make an extra call to the `/userinfo` endpoint of the IDP sim with the access token you returned at `/token`.
- Take a look here:

![USERINFO_1](https://i.imgur.com/Z6fZlKi.png)

You can see that rather than getting user data from the ID token, Okta is making an extra call to `/userinfo` with the access token our server returned in the `Authorization` header as a bearer token.

- For the sake of simplicity, I have our server returning `IDP_TEST_USER` for each of the base profile claims - a live IDP would be returning a unique sub claim as well as relevant information for the other values.

## Conclusion
Hopefully this demystifies some of the process of how Okta integrates with external IDPs. It's a lot of work to roll your own IDP, most developers use established IDPs. Maybe this repo can to troubleshoot those integrations as well.
