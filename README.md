# Spike crypto-bot


## Exporting conda env as .yml
1. Activate the env
2. `conda env export --from-history > environment.yml`  


## Creating conda env from .yml
1. `conda env create -f environment.yml`


# Coinbase User API Required Permissions

### `wallet:accounts:read`

This is needed because the bot is otherwise unable to retrieve information regarding the current state of the users
wallets which can be queried via the bot. Some of this information is also used in calculations for certain features.

### `wallet:transactions:read` 

This required for the bot to calculate the profits gained by selling a currency, and in order to generate account
specific graphs which show at what exchange rate transactions were made and how the value of user profiles changed.


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

A txt file which das a ``SINGLE LINE`` no white spaces containing the bot API key on the first line



## whitelist.json

A json file which contains the telegram usernames of authorized users, as well as optional passwords to activate personal statisics for accounts

```json
{
  "whitelisted": ["telegram_user1", "telegram_user2"],
  "password": []
}
```
