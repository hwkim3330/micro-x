# Cost model, not a production quote

Accessed 2026-09-08: Waveshare ST3215 family listing shows $16.99–21.99 (variant dependent). https://www.waveshare.com/product/modules/st3215-servo.htm

The website uses the low end as an **editable comparison input**, not a selected motor or BOM guarantee. The B2 website default uses the 14-axis compatibility target, $60 other components, $35 fabrication/assembly and 95% yield: `(14*16.99+60+35)/0.95 = $350.38`. Q4 is retired. The current compatibility study assumes XL330/BAM; this ST3215 comparison price is not an XL330 quote or a compatible BOM. These unquoted allowances are not market evidence. Changing motor count does not automatically create a mechanically feasible architecture.

Price excludes tax, freight, duties, tooling, development, certification, scrap rework beyond the simplified yield model, packaging, distribution, warranty and margin. Prices are USD; no exchange-rate conversion is asserted. For quantity pricing obtain written supplier quotes on a frozen revision.

## Cost reduction decisions

- Start with FDM prototypes, avoiding injection tooling before geometry and demand are validated.
- Use common M3 interfaces and serviceable shell halves, aiming to reduce fastener assortment and repair labor.
- Compare purchased serial-bus actuators rather than choosing from stall torque or unit price alone. Mass, continuous load, current, backlash, noise and thermal limits matter.
- Keep arms as passive mechanisms unless product behavior justifies added motors. B2 walking and Q4 quadruped platforms are now required; do not drop required degrees of freedom merely to hit a price.
- Record actual slicer mass, print time, assembly minutes, first-pass yield and failures after a physical build.

No percentage cost saving is claimed because neither a comparable baseline production BOM nor supplier quote is available.

The B2/Q4 candidate axis budgets and load assumptions are in `engineering/platforms.json`. The cheaper candidate does not pass the stated B2 torque screen. No procurement decision follows from the website calculator.
