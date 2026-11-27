
Alfred-Convert
==============

Convert between units in [Alfred][alfred], with or without an Internet connection. Alfred-Convert uses the [Pint][pintdocs] library, which knows hundreds of units. The workflow adds a few more, and you can add your own. Currency conversions need an Internet connection now and then to update exchange rates.

![][demo]

- [Installation](#installation)
- [Usage](#usage)
- [Currencies](#currencies)
  - [API keys](#api-keys)
  - [Active currencies](#active-currencies)
  - [Exchange rate updates](#exchange-rate-updates)
- [Configuration](#configuration)
- [Custom units](#custom-units)
- [Releases](#releases)
- [Thanks, copyright, licensing](#thanks-copyright-licensing)


Installation
------------

Download the workflow from [GitHub releases][ghreleases], then double-click the file to install it in Alfred.

Version 3.8 and later needs Python 3 (`/usr/bin/python3`) and works on macOS 12.3 or later with Alfred 5 or 6. If Python 3 isn't installed, macOS offers to install it (with the Xcode Command Line Tools) the first time you use the workflow.

If you still use Alfred 3, download [v3.6.2][v3.6.2] instead.


Usage
-----

Type `conv`, a number and a unit. To convert to a particular unit, add it at the end:

- `conv 128 mph kph`
- `conv 128 mph to kph` (`to`, `in`, `as`, `->` or `=` between the units is optional)
- `conv 72in cm` (the space after the number is optional)
- `conv 100psi bar`
- `conv 20.5 m/s mph`
- `conv 100 eur gbp`

The [cookbook](./docs/cookbook.md) has many more examples, with tips for writing numbers and units.

If you leave out the unit to convert to, the workflow uses your default units for that dimensionality, such as length or mass. To save a default, select a result and press `⌘↩`.

Some conversions only work in a [Pint context][pintcontexts]. Put the context's name or short name first: `conv spectroscopy 1Å eV` or `conv sp 1Å eV`.

If the workflow doesn't understand your query or doesn't know a unit, it says so.

When you select a result:

| Key  | Action                                                           |
|------|------------------------------------------------------------------|
| `↩`  | Copy the result without thousands separators                     |
| `⌘C` | Copy the result with thousands separators                        |
| `⌘↩` | Save the unit as a default for this dimensionality, or remove it |
| `⌘L` | Show the result in Large Type                                    |

Copied results leave out the unit unless you turn on `COPY_UNIT` in the [configuration sheet](#configuration).

Type `convinfo` for help and the workflow's files:

- **View Help File** opens this page.
- **View All Supported Currencies** lets you search the currency list.
- **Edit Active Currencies** opens your list of [active currencies](#active-currencies).
- **Edit Custom Units** opens your [custom units](#custom-units) file.


Currencies
----------

Use a currency's symbol, e.g. `conv 100 eur gbp`. See the [list of supported currencies](./docs/currencies.md), or search it in Alfred with `convinfo` → **View All Supported Currencies**.

Exchange rates come from:

- **[ExchangeRate-API.com][xapi]**: most fiat currencies, with no API key.
- **[openexchangerates.org][openx]**: fiat currencies, including the few ExchangeRate-API.com doesn't offer, if you set `APP_KEY`. It replaces ExchangeRate-API.com.
- **[CryptoCompare][cryptocompare]**: cryptocurrencies, if you set `CRYPTO_API_KEY`.


### API keys ###

Both keys are free. Set them in the [configuration sheet](#configuration):

- **`APP_KEY`**: [sign up for a free openexchangerates.org account][openx-free], then copy your **App ID** from the sign-up email or [your account page][openx-appid].
- **`CRYPTO_API_KEY`**: get a free CryptoCompare API key from [CoinDesk][coindesk-key].

If a currency has no exchange rate, the workflow tells you which API key adds it. A currency also needs to be in your [active currencies](#active-currencies).


### Active currencies ###

The workflow downloads exchange rates only for active currencies. By default, these are all supported fiat currencies and a handful of popular cryptocurrencies, such as BTC and ETH.

To change the list, use `convinfo` → **Edit Active Currencies**, and put one currency symbol on each line. To find a symbol, use `convinfo` → **View All Supported Currencies**, select the currency and press `⌘C` to copy its symbol.


### Exchange rate updates ###

The workflow updates exchange rates in the background every 6 hours. To change how often, set `UPDATE_INTERVAL` (in minutes). While an update runs, Alfred shows "Updating exchange rates…" above the results.

If an update fails, e.g. because you're offline, the workflow keeps using the rates it already has and tries again after 5 minutes. When you set or remove an API key, the workflow deletes its saved rates and downloads new ones.


Configuration
-------------

Set these variables in the workflow's [configuration sheet][config-sheet] (the `[𝒙]` button in Alfred Preferences):

| Variable                  | Meaning                                                                                                 | Default |
|---------------------------|---------------------------------------------------------------------------------------------------------|---------|
| `APP_KEY`                 | API key for openexchangerates.org. See [API keys](#api-keys).                                           | None    |
| `COPY_UNIT`               | Include the unit when copying a result. Any value except `0` or empty turns this on.                    | Off     |
| `CRYPTO_API_KEY`          | API key for CryptoCompare. See [API keys](#api-keys).                                                   | None    |
| `CURRENCY_DECIMAL_PLACES` | Decimal places in currency results. If empty, `DECIMAL_PLACES` is used.                                 | `2`     |
| `DECIMAL_PLACES`          | Decimal places in results.                                                                              | `2`     |
| `DECIMAL_SEPARATOR`       | Character between whole numbers and decimal fractions, in queries and results.                          | `.`     |
| `DYNAMIC_DECIMALS`        | Add decimal places (up to 10) until the result isn't zero. Any value except `0` or empty turns this on. | On      |
| `THOUSANDS_SEPARATOR`     | Character between groups of thousands, in queries and results.                                          | `,`     |
| `UPDATE_INTERVAL`         | Minutes between exchange rate updates.                                                                  | `360`   |


Custom units
------------

Add your own units to `unit_definitions.txt` in the workflow's data folder. To open it, use `convinfo` → **Edit Custom Units**. Define each unit in [Pint's format][pinthowto]. Pint's [default definitions][pintunits] have many examples.

If you think a unit would be useful to everyone, please [open an issue][ghissues] or send a [pull request][ghpulls].


Releases
--------

See the [changelog][changelog] for what changed in each version. From version 3.8, releases are on [this repository's releases page][ghreleases]. Earlier releases are on the [original repository's releases page][upstream-releases].


Thanks, copyright, licensing
----------------------------

- This is a fork of [deanishe/alfred-convert][upstream] by Dean Jackson.
- The [Pint][pintdocs] library does the unit conversions. See the [Pint repository][pintrepo] for its licence.
- Exchange rates come from [ExchangeRate-API.com][xapi], [openexchangerates.org][openx] and [CryptoCompare][cryptocompare].
- The workflow uses the [Alfred-PyWorkflow][alfred-pyworkflow] library.
- The icons are from [Font Awesome][fontawesome].

All other code and media are released under the [MIT Licence][mit].


[alfred]: https://www.alfredapp.com/
[alfred-pyworkflow]: https://xdevcloud.de/alfred-pyworkflow/
[changelog]: ./CHANGELOG.md
[coindesk-key]: https://developers.coindesk.com/
[config-sheet]: https://www.alfredapp.com/help/workflows/advanced/variables/#environment
[cryptocompare]: https://www.cryptocompare.com/
[demo]: ./demo.gif
[fontawesome]: https://fontawesome.com/
[ghissues]: https://github.com/bbrown/alfred-convert/issues
[ghpulls]: https://github.com/bbrown/alfred-convert/pulls
[ghreleases]: https://github.com/bbrown/alfred-convert/releases
[mit]: https://opensource.org/licenses/MIT
[openx]: https://openexchangerates.org/
[openx-appid]: https://openexchangerates.org/account/app-ids
[openx-free]: https://openexchangerates.org/signup/free
[pintcontexts]: https://pint.readthedocs.io/en/stable/user/contexts.html
[pintdocs]: https://pint.readthedocs.io/
[pinthowto]: https://pint.readthedocs.io/en/stable/advanced/defining.html
[pintrepo]: https://github.com/hgrecco/pint
[pintunits]: https://github.com/hgrecco/pint/blob/master/pint/default_en.txt
[upstream]: https://github.com/deanishe/alfred-convert
[upstream-releases]: https://github.com/deanishe/alfred-convert/releases
[v3.6.2]: https://github.com/deanishe/alfred-convert/releases/tag/v3.6.2
[xapi]: https://www.exchangerate-api.com/
