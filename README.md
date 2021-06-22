# crypto-bot


## Exporting conda env as .yml
1. Activate the env
2. `conda env export --from-history > environment.yml`  


## Creating conda env from .yml
1. `conda env create -f environment.yml`



# Required Files

### Note: All these files should be located in a directory called ```credentials```


## API_key.json

This contains the API keys for coinbase and coinbase pro, along with the secret key

```json
{
    "key": "<coinbase-api-key>",
    "secret": "<coinbase-secret>",
    "cbpro_key": "<coinbase-pro-api-key>",
    "cbpro_secret": "<coinbase-pro-secret>",
    "cbpro_passphrase": "<coinbase-pro-passphrase>"
}
```


## telegram-bot-api-key.txt

A txt file which has a ``SINGLE LINE`` no white spaces containing the bot API key on the first line



## whitelist.json

A json file which contains the telegram usernames of authorized users, as well as optional passwords to activate personal statisics for accounts

```json
{
  "whitelisted": ["telegram_user1", "telegram_user2"],
  "password": []
}
```
