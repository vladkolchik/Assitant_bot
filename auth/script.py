from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

SCOPES = ["https://mail.google.com/"]

flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
creds = flow.run_local_server(port=0)

with open("token.pkl", "wb") as token_file:
    pickle.dump(creds, token_file)
