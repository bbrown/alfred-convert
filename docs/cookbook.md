
Cookbook
========

<!--
src/test_cookbook.py runs every example in the ```text blocks below. Each
"conv <query> → <result>" line must show what Alfred shows with the default
settings in src/info.plist. Put further results of the same query on the
next lines, starting with "→". The ```ini block holds custom units the
examples use, and the two tables set the exchange rates and saved defaults.
-->

Recipes for the `conv` keyword, from everyday conversions to a few tricks. Each example shows what Alfred displays with the workflow's default settings.

- [The shape of a query](#the-shape-of-a-query)
- [Reading the results](#reading-the-results)
- [Writing numbers](#writing-numbers)
- [Writing units](#writing-units)
- [Length and distance](#length-and-distance)
- [Area](#area)
- [Volume and cooking](#volume-and-cooking)
- [Mass and weight](#mass-and-weight)
- [Temperature](#temperature)
- [Speed and pace](#speed-and-pace)
- [Time](#time)
- [Data and transfer rates](#data-and-transfer-rates)
- [Energy and power](#energy-and-power)
- [Pressure](#pressure)
- [Angles](#angles)
- [Other compound units](#other-compound-units)
- [Currencies](#currencies)
- [Default units](#default-units)
- [Contexts](#contexts)
- [Your own units](#your-own-units)
- [When something goes wrong](#when-something-goes-wrong)


The shape of a query
--------------------

Type `conv`, a number, the unit to convert from and the unit to convert to:

```text
conv 26.2 mi km           → 42.16 km
conv 26.2mi km            → 42.16 km
conv 26.2 mi to km        → 42.16 km
conv 12 in in cm          → 30.48 cm
conv 12 m in              → 472.44 in
```

The space between the number and the unit is optional. You can put `to`, `in`, `as`, `->` or `=` between the units. A lone `in` at the end is inches, as in the last line. If you leave out the unit to convert to, the workflow uses your [default units](#default-units).

To see several results at once, add more units:

```text
conv 1 kg lb oz           → 2.20 lb
                          → 35.27 oz
```


Reading the results
-------------------

A result shows the number and the unit's symbol, so `miles` comes back as `mi`. Numbers have 2 decimal places and a `,` between thousands. Small results get extra decimal places, up to 10, so they don't round to zero. Even smaller results use scientific notation:

```text
conv 1 km mm              → 1,000,000.00 mm
conv 15 mm m              → 0.015 m
conv 1 mm km              → 0.000001 km
conv 1 barn m^2           → 1.00e-28 m²
```

To change how numbers look, set `DECIMAL_PLACES`, `DYNAMIC_DECIMALS`, `DECIMAL_SEPARATOR` and `THOUSANDS_SEPARATOR` in the [configuration sheet](../README.md#configuration). [Usage](../README.md#usage) lists the keys for copying a result, saving a default and Large Type.


Writing numbers
---------------

Use `.` for decimals and `,` between thousands. A leading `-` makes a number negative:

```text
conv 2.5 cm in            → 0.98 in
conv .5 m cm              → 50.00 cm
conv 1,500 m km           → 1.50 km
conv -40 degC degF        → -40.00 °F
```

A `,` needs 3 digits after it, so the workflow won't quietly read `1,5` as 15:

```text
conv 1,5 m cm             → Use "." for decimals and "," between thousands
```

Fractions, vulgar fractions such as `½`, and scientific notation work too:

```text
conv 1/2 cup ml           → 118.29 ml
conv 1 1/2 cups ml        → 354.88 ml
conv 1½ cups ml           → 354.88 ml
conv 1e3 m km             → 1.00 km
conv 2.5e-6 m nm          → 2,500.00 nm
```

A minus sign copied from a web page (`−`) works like `-`. If you change `DECIMAL_SEPARATOR` or `THOUSANDS_SEPARATOR`, write numbers that way, e.g. `2,5` with a `,` decimal separator.


Writing units
-------------

Use a unit's symbol, its name or its plural:

```text
conv 3 ft m               → 0.91 m
conv 3 feet m             → 0.91 m
conv 3 foot meters        → 0.91 m
```

Put an SI prefix on any unit. Type `u` for micro (µ):

```text
conv 2 GHz MHz            → 2,000.00 MHz
conv 1500 um mm           → 1.50 mm
```

Units are case-sensitive. `MB` is megabytes, but `mb` is millibarns:

```text
conv 1 MB kB              → 1,000.00 kB
conv 1 mb kb              → 0.000001 kb
```

Build compound units with `/` (or the word `per`), `*` and powers (`^2`, `**2` or `²`). Don't put other spaces inside a unit:

```text
conv 3 m^2 ft^2                 → 32.29 ft²
conv 100 ft² m²                 → 9.29 m²
conv 1 m**3 l                   → 1,000.00 l
conv 10 m/s km/h                → 36.00 km/h
conv 60 miles per hour km per h → 96.56 km/h
conv 100 N*m ft*lbf             → 73.76 ft·lbf
```


Length and distance
-------------------

```text
conv 5 km mi              → 3.11 mi
conv 6 ft cm              → 182.88 cm
conv 70 in cm             → 177.80 cm
conv 1 nmi km             → 1.85 km
conv 1 au km              → 149,597,870.70 km
conv 1 pc ly              → 3.26 ly
conv 5 ft 10 in cm        → 177.80 cm
conv 5'10" cm             → 177.80 cm
conv 1.8 m ft+in          → 5 ft 10.87 in
```

`nmi` is a nautical mile, `au` an astronomical unit, `pc` a parsec and `ly` a light year. For feet and inches, write both, or use `'` and `"`. To get feet and inches back, join the units with `+`, as in the last line.


Area
----

```text
conv 1 acre m^2           → 4,046.87 m²
conv 1 ha acre            → 2.47 acre
conv 2000 sq_ft m^2       → 185.81 m²
conv 1 km^2 mi^2          → 0.39 mi²
```

`ha` is a hectare. Write square units with a power, or use Pint's `sq_` names such as `sq_ft`.


Volume and cooking
------------------

```text
conv 1 gal l              → 3.79 l
conv 1 UK_gallon l        → 4.55 l
conv 1 pint ml            → 473.18 ml
conv 1 UK_pint ml         → 568.26 ml
conv 2 cups ml            → 473.18 ml
conv 1 cup tbsp           → 16.00 tbsp
conv 1 tbsp tsp           → 3.00 tsp
conv 12 floz ml           → 354.88 ml
conv 350 degF degC        → 176.67 °C
```

Gallons, pints, cups and fluid ounces are US measures. For UK measures, start the name with `UK_`. The last line converts an oven temperature.


Mass and weight
---------------

```text
conv 70 kg lb             → 154.32 lb
conv 1 lb g               → 453.59 g
conv 12 oz g              → 340.19 g
conv 11 stone kg          → 69.85 kg
conv 1 t lb               → 2,204.62 lb
conv 1 ton kg             → 907.18 kg
conv 1 ozt g              → 31.10 g
conv 100 kg stone+lb      → 15 stone 10.46 lb
conv 11 st 4 lb kg        → 71.67 kg
```

`t` is a metric tonne and `ton` a US short ton. `st` is a stone. `ozt` is a troy ounce, used for precious metals.


Temperature
-----------

```text
conv 20 degC degF                → 68.00 °F
conv 98.6 degF degC              → 37.00 °C
conv 20 °C °F                    → 68.00 °F
conv 20 celsius fahrenheit       → 68.00 °F
conv 300 K degC                  → 26.85 °C
conv 10 delta_degC delta_degF    → 18.00 Δ°F
```

Write degrees as `degC`, `°C` or `celsius`, and the same way for Fahrenheit. `K` is kelvin. These convert a temperature from one scale to another. To convert a change in temperature, such as a rise of 10 °C, use `delta_degC` and `delta_degF`.


Speed and pace
--------------

```text
conv 100 km/h mph         → 62.14 mph
conv 60 mph kph           → 96.56 kph
conv 20 knots km/h        → 37.04 km/h
conv 20 kn mph            → 23.02 mph
conv 5 min/km min/mi      → 8:03 min/mi
conv 5 min/km km/h        → 12.00 km/h
conv 10 mph min/mi        → 6:00 min/mi
```

Divide a distance by a time, or use `mph`, `kph`, `knots` or `kn`. A running pace is a time divided by a distance, as in the last three lines, and shows minutes and seconds. Pace and speed are inverses, and the workflow converts between them.


Time
----

```text
conv 90 min h             → 1.50 h
conv 2.5 h min            → 150.00 min
conv 3 weeks days         → 21.00 d
conv 1 year days          → 365.25 d
conv 1 century years      → 100.00 yr
conv 1h30min min          → 90.00 min
conv 1000000 s d+h+min+s  → 11 d 13 h 46 min 40 s
```

A `year` is 365.25 days. Mixed times work too, but write minutes as `min`: `m` is a metre.


Data and transfer rates
-----------------------

```text
conv 1 GB MB              → 1,000.00 MB
conv 1 GiB MiB            → 1,024.00 MiB
conv 500 GB GiB           → 465.66 GiB
conv 100 Mbit/s MB/s      → 12.50 MB/s
```

`B` is a byte and `bit` is a bit. `kB`, `MB` and `GB` count in thousands, while `KiB`, `MiB` and `GiB` count in 1,024s. That's why a 500 GB drive shows up as 465 GB in some apps. Internet speeds are usually in megabits per second (`Mbit/s`).


Energy and power
----------------

```text
conv 1 kWh MJ             → 3.60 MJ
conv 2000 kcal kJ         → 8,368.00 kJ
conv 2000 Cal kJ          → 8,368.00 kJ
conv 150 hp kW            → 111.85 kW
conv 100 W BTU/h          → 341.21 Btu/h
conv 1 boe GJ             → 6.12 GJ
```

`kcal` or `Cal` is the food Calorie. `hp` is mechanical horsepower. `boe` is a barrel of oil equivalent, the energy in a barrel of crude oil.


Pressure
--------

```text
conv 32 psi bar           → 2.21 bar
conv 1 atm kPa            → 101.33 kPa
conv 1013 hPa inHg        → 29.91 inHg
```

Weather reports use hectopascals (`hPa`) or inches of mercury (`inHg`).


Angles
------

```text
conv 90 deg rad           → 1.57 rad
conv 1 rad deg            → 57.30 deg
conv 1 turn deg           → 360.00 deg
```


Other compound units
--------------------

```text
conv 30 mi/gal km/l       → 12.75 km/l
conv 30 mpg km/l          → 12.75 km/l
conv 30 mpg l/100km       → 7.84 l/100km
conv 1 g/cm^3 kg/m^3      → 1,000.00 kg/m³
conv 10 gal/min l/s       → 0.63 l/s
conv 1 g0 m/s^2           → 9.81 m/s²
conv 0.07 l/km l/100km    → 7.00 l/100km
conv 30 kWh/100mi kWh/100km → 18.64 kWh/100km
conv 50 Hz ms             → 20.00 ms
```

`mpg` is miles per US gallon, the same as `mi/gal`. Litres per kilometre is the inverse of kilometres per litre, so the workflow divides 1 by the number to convert between them. It does the same for any units that are inverses, such as a frequency (`Hz`) and the time of one cycle (`ms`). `g0` is standard gravity. A unit can include a number, such as `l/100km` for litres per 100 km or `kWh/100mi` for an electric car's consumption.


Currencies
----------

Use a currency's three-letter code, in upper or lower case. See the [supported currencies](./currencies.md). The workflow downloads exchange rates in the background, so your results depend on the day's rates. These examples use made-up rates:

| Currency | Per US dollar |
|----------|---------------|
| EUR      | 0.92          |
| GBP      | 0.79          |
| JPY      | 150           |
| PHP      | 58            |

```text
conv 100 eur usd          → 108.70 USD
conv 100 USD EUR          → 92.00 EUR
conv 5,000 jpy usd        → 33.33 USD
conv 1000 php usd         → 17.24 USD
conv $100 eur             → 92.00 EUR
conv 100€ usd             → 108.70 USD
conv £20 $                → 25.32 USD
```

You can also write `$`, `€`, `£`, `¥`, `₹` or `₿`, before or after the number. `$` is the US dollar and `¥` the Japanese yen.

Prefixes work on currencies too: `kEUR` is thousands of euros. Prices per unit convert as well:

```text
conv 1.5 kEUR usd         → 1,630.43 USD
conv 5 usd/lb eur/kg      → 10.14 EUR/kg
conv 4 usd/gal eur/l      → 0.97 EUR/l
```

Without an API key, a few currencies (such as gold, `XAU`) and all cryptocurrencies have no exchange rates. The workflow tells you which key to set, and selecting the message opens the instructions. See [API keys](../README.md#api-keys).

```text
conv 1 xau usd            → Set APP_KEY to convert this currency
conv 1 eth usd            → Set CRYPTO_API_KEY to convert this currency
```

A currency also needs to be in your [active currencies](../README.md#active-currencies). Currency results use `CURRENCY_DECIMAL_PLACES`.


Default units
-------------

If you leave out the unit to convert to, the workflow converts to your default units for that dimensionality, such as length, mass or currency. To save a default, select a result and press `⌘↩`. To remove one, press `⌘↩` on it again. These examples assume you've saved these defaults:

| Dimensionality  | Default units       |
|-----------------|---------------------|
| `[currency]`    | `EUR`, `GBP`        |
| `[temperature]` | `degree_Fahrenheit` |

```text
conv 100 usd              → 92.00 EUR
                          → 79.00 GBP
conv 100 eur              → 85.87 GBP
conv 20 degC              → 68.00 °F
conv 5 kg                 → No destination units (or defaults) for [mass]
```

The workflow skips a default that's the same as the unit you convert from, so `100 eur` only shows pounds. With no defaults for a dimensionality, it says so.


Contexts
--------

Some conversions link different kinds of quantity through physics, such as the wavelength and frequency of light. Pint only does these in a [context][pintcontexts]. Put the context's name first:

```text
conv sp 500 nm THz           → 599.58 THz
conv sp 2.5 eV nm            → 495.94 nm
conv spectroscopy 1Å eV      → 12,398.42 eV
conv boltzmann 300 K meV     → 25.85 meV
conv Gau 1 T G               → 10,000.00 G
```

`spectroscopy`, or `sp` for short, links wavelength, frequency and photon energy. `boltzmann` links temperature and energy. `Gaussian`, or `Gau`, converts SI electromagnetic units, such as teslas, to Gaussian units, such as gauss. The workflow reads the letters before the number as a context name.


Your own units
--------------

Add units to `unit_definitions.txt` with `convinfo` → **Edit Custom Units**, one per line in [Pint's format][pinthowto]. A unit can build on any other unit, including a currency:

```ini
marathon = 42.195 km
bigmac = 5.69 USD
```

```text
conv 1 marathon mi        → 26.22 mi
conv 3 bigmac eur         → 15.70 EUR
```


When something goes wrong
-------------------------

```text
conv km m                 → Unknown context: km
conv 3 furlongz m         → Unknown unit: furlongz
conv 1 m s                → Can't convert from m [length] to s [time]
conv 5 ft 10 kg m         → Can't add kg to ft
conv 5 m / s kph          → Unknown unit: /
```

- A query must start with a number. The workflow reads letters before the number as a [context](#contexts) name.
- If the workflow doesn't know a unit, check the spelling or look it up in Pint's [list of units][pintunits].
- You can only convert between units of the same kind. The message shows each unit's dimensionality.
- Don't put spaces inside a unit: write `m/s`.


[pintcontexts]: https://pint.readthedocs.io/en/stable/user/contexts.html
[pinthowto]: https://pint.readthedocs.io/en/stable/advanced/defining.html
[pintunits]: https://github.com/hgrecco/pint/blob/master/pint/default_en.txt
