
Changelog
=========

### [3.9.0][v3.9.0] ###

Released 2026-11-26

- Write `to`, `in`, `as`, `->` or `=` between units, and `per` for `/`, e.g. `conv 26.2 mi to km` or `conv 60 miles per hour kph`
- Convert to several units at once, e.g. `conv 1 kg lb oz`
- Convert mixed amounts such as `5 ft 10 in`, `5'10"` or `1h30min`, and show results in mixed units joined with `+`: `conv 1.8 m ft+in` shows `5 ft 10.87 in`
- Read fractions, vulgar fractions and scientific notation, e.g. `1/2 cup`, `1½ cups` or `1e3 m`, and the minus sign `−` that web pages use
- Read the currency symbols `$`, `€`, `£`, `¥`, `₹` and `₿`, e.g. `conv $100 eur`
- Allow a number in a unit, e.g. `l/100km` or `kWh/100mi`
- Convert between reciprocal units, such as pace and speed (`5 min/km km/h`) or fuel economy and consumption (`30 mpg l/100km`)
- Allow contexts whose names start with a capital, such as `Gaussian`
- Show unit symbols in results, e.g. `°F` and `km/h` instead of `degree_Fahrenheit` and `kilometer_per_hour`
- Show a pace in minutes and seconds, e.g. `8:03 min/mi`, and tiny results in scientific notation instead of `0.00`
- Show the exchange rate and its age under currency results
- Show the nearest measuring cup or spoon amount under results in cups, tablespoons and teaspoons
- Point out temperatures below absolute zero
- Suggest the closest unit for an unknown one: `↩` or `⇥` puts it in the query
- Press `⇥` on a result to convert it further
- Name dimensionalities in messages, e.g. `density` instead of `[mass] / [length] ** 3`
- Add default units for length, mass, temperature, area, volume, speed, time and currency, until you save your own
- Add the units `mpg`, `kn`, `st` and `Cal`, the cooking units `pinch`, `dash`, `drop`, `jigger` and `stick`, the counting units `dozen`, `bakers_dozen`, `score` and `gross`, and, just for fun, `smoot`, `banana`, `football_field`, `olympic_pool`, `beard_second`, `sheppey`, `light_second`, `firkin` and `cubit`
- `boe` is now energy (5.8 million Btu), not a volume of gas, so `1 boe GJ` works but `1 MMscf boe` no longer does
- Speed up conversions that don't involve a currency by about 30%
- Remove the docopt library
- Fix small results losing a digit, e.g. `15 mm m` showed `0.01` instead of `0.015`
- Fix lowercase `php`, `myr`, `khr` and `kyd` converting as picohorsepower, milliyear, kilohour and kiloyard instead of currencies
- Fix half-typed queries (e.g. `-` or `20.5 m/`) showing a raw Python or workflow error
- Fix `+` or `-` between units (e.g. `1 m ft-in`) showing a raw Python error
- Fix a setting that isn't a whole number (e.g. `DECIMAL_PLACES=2.5`) stopping the workflow: `DECIMAL_PLACES`, `CURRENCY_DECIMAL_PLACES` and `UPDATE_INTERVAL` now fall back to their defaults
- Fix a saved default that no longer exists, such as an inactive currency, stopping the workflow
- Fix `1,5 m cm` converting 15 m: a thousands separator now needs 3 digits after it
- Fix Réaumur conversions: 80 °Re is 100 °C, not 64 °C
- Fix `1 pinch ml` converting picoinches, and `1 drop ml` asking for `CRYPTO_API_KEY`
- Add a [cookbook](./docs/cookbook.md) of example conversions and tips for writing queries


### [3.8.0][v3.8.0] ###

Released 2026-11-25

- Port to Python 3 (`/usr/bin/python3`): works on macOS 12.3+ and Alfred 5/6
- Update Pint to 0.24.4 and replace Alfred-Workflow with Alfred-PyWorkflow
- Some units now display with Pint's current names, e.g. `kph` → `kilometer_per_hour`, `degF` → `degree_Fahrenheit`
- Cryptocurrency rates require a CryptoCompare API key (`CRYPTO_API_KEY`, optional). Without it, crypto rates are skipped instead of breaking all currency updates
- Remove update checks against the archived upstream repo
- Fix negative results showing 10 decimal places
- Fix a leading `+` (e.g. `+5km m`) swallowing the first letter of the unit
- Fix Bitcoin not converting when only `CRYPTO_API_KEY` is set
- Fix a currency symbol Pint can't use (e.g. `STR*`) breaking every conversion
- Wait 5 minutes between exchange rate download attempts when offline
- Show which API key adds an unknown currency, and show no error while rates download
- Add fiat currencies `SLE`, `VES`, `XCG`, `ZWG` and `ZWL` (in an existing install, add them to your active currencies to use them)
- Open this fork's README and issues from help links


### [3.7.0][v3.7.0] ###

Released 2020-02-20

- Add exchange rates from ExchangeRate-API.com (no API key required)


### [3.6.2][v3.6.2] ###

Released 2019-09-06

- Include `pkg_resources` (Pint dependency)


### [3.6.1][v3.6.1] ###

Released 2019-05-30

- Fix argument quoting


### [3.6.0][v3.6.0] ###

Released 2019-05-06

- Alfred 4 support.


### [3.5.3][v3.5.3] ###

Released 2019-01-26

- Swap `⌘C` and `↩` to match Alfred's behaviour. `↩` copies result without thousands separator and `⌘C` copies result with separator.


### [3.5.2][v3.5.2] ###

Released 2019-01-26

- Copy result with or without thousands separator.



### [3.5.1][v3.5.1] ###

Released 2018-01-13

- Add `CURRENCY_DECIMAL_PLACES` setting to provide alternate number of decimal places for currency conversions.


### [3.5][v3.5] ###

Released 2018-01-12

- Add `DYNAMIC_DECIMALS` setting to expand the number of decimal places until the displayed result is non-zero.


### [3.4][v3.4] ###

Released 2017-12-27

- Understand negative numbers in input


### [3.3.1][v3.3.1] ###

Released 2017-11-21

- Disable currencies with conflicting symbols


### [3.3][v3.3] ###

Released 2017-11-20

- Parse numbers in accordance with the decimal and thousands separators specified in the workflow configuration

### [3.2.2][v3.2.2] ###

Released 2017-11-07

- Show warning if user tries to convert fiat currency and `APP_KEY` isn't set
- Ensure cache is cleared after user sets `APP_KEY`

### [3.2.1][v3.2.1] ###

Released 2017-11-04

- Clear cached data when updated from v<3.1 or when `APP_KEY` is set.


### [3.2][v3.2] ###

Released 2017-11-02.

- Add support for Pint's contexts #18


### [3.1][v3.1] ###

Released 2017-11-02.

- Replace Yahoo! Finance with [openexchangerates.org][openx] #27


### [3.0][v3.0] ###

Released 2017-07-16.

- Option to exclude units when copying #12
- Add per-dimensionality defaults #13
- Option to specify thousands separator #15
- Option to specify custom decimal separator #16
- Add cryptocurrencies #21
- Update Alfred-Workflow
- Update Pint


### [2.6][v2.6] ###

Released 2017-06-15.

- Fix Sierra forking issue


### [2.5][v2.5] ###

Released 2015-12-11.

- Fix decoding error


### [2.4][v2.4] ###

Released 2015-11-28.

- New money icon
- Update pint, docopt and Alfred-Workflow libraries
- Reorganise code and repo


### [2.3][v2.3] ###

Released 2015-11-26.

- Prevent currencies from clobbering existing units #7
- More precise error messages
- Better query parsing


### [2.2.1][v2.2.1] ###

Released 2015-07-16.

- Use HTTPS to fetch exchange rates #5
- Improve self-updating
- Use online README instead of bundled file


### [2.2][v2.2] ###

Released 2015-07-15.

- Add Bitcoin exchange rate #6


### 2.1 ###

Never released.

- Update Alfred-Workflow


### [2.0][v2.0] ###

Released 2014-12-26.

- Add support for 150+ currencies via Yahoo! Finance #1 #3
- Add support for custom user unit definitions
- Add some additional units to workflow #4
- Configurable number of decimal places in results
- Automatically check for updates (and offer to install them)


### [1.2][v1.2] ###

Released 2014-08-19.

- Properly handle units containing uppercase letters #2


### [1.1][v1.1] ###

Released 2014-08-09.

- First release

[v1.1]: https://github.com/deanishe/alfred-convert/releases/tag/v1.1
[v1.2]: https://github.com/deanishe/alfred-convert/releases/tag/v1.2
[v2.0]: https://github.com/deanishe/alfred-convert/releases/tag/v2.0
[v2.2.1]: https://github.com/deanishe/alfred-convert/releases/tag/v2.2.1
[v2.2]: https://github.com/deanishe/alfred-convert/releases/tag/v2.2
[v2.3]: https://github.com/deanishe/alfred-convert/releases/tag/v2.3
[v2.4]: https://github.com/deanishe/alfred-convert/releases/tag/v2.4
[v2.5]: https://github.com/deanishe/alfred-convert/releases/tag/v2.5
[v2.6]: https://github.com/deanishe/alfred-convert/releases/tag/v2.6
[v3.0]: https://github.com/deanishe/alfred-convert/releases/tag/v3.0
[v3.1]: https://github.com/deanishe/alfred-convert/releases/tag/v3.1
[v3.2]: https://github.com/deanishe/alfred-convert/releases/tag/v3.2
[v3.2.1]: https://github.com/deanishe/alfred-convert/releases/tag/v3.2.1
[v3.2.2]: https://github.com/deanishe/alfred-convert/releases/tag/v3.2.2
[v3.3]: https://github.com/deanishe/alfred-convert/releases/tag/v3.3
[v3.3.1]: https://github.com/deanishe/alfred-convert/releases/tag/v3.3.1
[v3.4]: https://github.com/deanishe/alfred-convert/releases/tag/v3.4
[v3.5]: https://github.com/deanishe/alfred-convert/releases/tag/v3.5
[v3.5.1]: https://github.com/deanishe/alfred-convert/releases/tag/v3.5.1
[v3.5.2]: https://github.com/deanishe/alfred-convert/releases/tag/v3.5.2
[v3.5.3]: https://github.com/deanishe/alfred-convert/releases/tag/v3.5.3
[v3.6.0]: https://github.com/deanishe/alfred-convert/releases/tag/v3.6.0
[v3.6.1]: https://github.com/deanishe/alfred-convert/releases/tag/v3.6.1
[v3.6.2]: https://github.com/deanishe/alfred-convert/releases/tag/v3.6.2
[v3.7.0]: https://github.com/deanishe/alfred-convert/releases/tag/v3.7.0
[v3.8.0]: https://github.com/bbrown/alfred-convert/releases/tag/v3.8.0
[v3.9.0]: https://github.com/bbrown/alfred-convert/releases/tag/v3.9.0
[openx]: https://openexchangerates.org/