# One-off script used to write data/cities/boston.json from sources verified on 2026-10-21.
# Raw page snapshots used for verification are in research/boston/.
import json
NS = "Not stated, check with them"
D = "2026-10-21"
BOS_TRASH = "https://www.boston.gov/departments/public-works/trash"
BOS_MATT = "https://www.boston.gov/departments/public-works/mattress-recycling"
BOS_SPEC = "https://www.boston.gov/departments/public-works/special-collection-items"
BOS_LARGE = "https://www.boston.gov/departments/public-works/large-residential-buildings"
BOS_CIRC = "https://www.boston.gov/sites/default/files/file/2024/04/Boston%27s%20Circular%20Economy%20Directory_0.pdf"
CITYLIST_NOTE = "Listed by the City of Boston on its mattress-hauler list for large residential buildings; details below are as the City lists them. Confirm directly with the company."

def L(**k):
    base = dict(items_not_accepted=[], address=None, notes=None, book_url=None, phone=None, email=None,
                condition_rules=NS, stairs_inside=NS, lead_time=NS, cost=NS, service_area=NS, last_verified=D)
    base.update(k); return base

listings = [
 L(id="boston-curbside-furniture", name="City of Boston curbside furniture collection", type="city bulk pickup",
   items_accepted=["Furniture"],
   condition_rules="Put furniture out with your normal curbside trash and recycling on your scheduled collection day, placed neatly next to your trash receptacles. Trash must be curbside by 6 a.m.; don't put it out before 5 p.m. the evening before. The City does not collect construction debris, plumbing fixtures, water heaters, fences, or auto parts.",
   stairs_inside="No. Curbside only; the City will not pick up on private property.",
   lead_time="Your regular trash collection day (find it in the Trash Day app or the City's schedule search).",
   cost="No fee is mentioned on the City page. Check with 311 if unsure.",
   service_area="Addresses that receive City of Boston curbside trash collection. Large buildings (7+ units) should check the City's large-building page and their property manager.",
   book_url="https://www.boston.gov/departments/public-works/trash-and-recycling-day-schedule-and-search", phone="311 or 617-635-4500", email="311@boston.gov",
   source_urls=[BOS_TRASH, BOS_LARGE]),
 L(id="boston-mattress-recycling", name="City of Boston curbside mattress & box spring recycling (appointment)", type="city bulk pickup",
   items_accepted=["Mattresses (memory foam, innerspring, hybrid, latex)", "Box springs"],
   items_not_accepted=["Futons", "Mattress toppers", "Other non-mattress items (these can go out with curbside trash)"],
   condition_rules="Appointment required; mattresses are not collected with regular trash (Massachusetts waste ban). Soiled, dirty, or bed-bug mattresses must be bagged and fully sealed. Do not crush or cut the mattress. Place curbside by 6 a.m. on your appointment day (or after 5 p.m. the night before), not blocked and with nothing on top. Limit: 10 items per calendar year. Cancel before 12 p.m. the day before.",
   stairs_inside="No. Curbside only; items on private property are not collected.",
   lead_time=NS,
   cost="No fee is mentioned on the City page. Check with 311 if unsure.",
   service_area="City of Boston residents in buildings with 6 units or fewer. Buildings with more units must use their property manager or a private hauler.",
   book_url=BOS_MATT + "#schedule-pickup", phone="311 or 617-635-4500", email="311@boston.gov",
   source_urls=[BOS_MATT]),
 L(id="boston-special-items", name="City of Boston special item collection (fridges, ACs, TVs, monitors)", type="city bulk pickup",
   items_accepted=["Refrigerators & freezers", "Air conditioners", "Dehumidifiers", "Water coolers", "Ice makers", "Televisions", "Computer monitors", "Laptops"],
   items_not_accepted=["Commercial-grade items", "Dishwashers, water heaters, plumbing fixtures (donate or hire a private hauler)"],
   condition_rules="Appointment required. Remove all fridge/freezer doors (including mini-fridges) and all food, or the item won't be collected. Don't smash appliances or electronics. Wipe data from computers. TVs and computers must be freestanding, not boxed. Max 5 items per appointment and 10 per calendar year. Cancel before 12 p.m. the day before.",
   stairs_inside="No. Place it where trash is collected (curbside, public alley, or dumpster area); items on private property are not collected.",
   lead_time=NS,
   cost="No fee is mentioned on the City page. Check with 311 if unsure.",
   service_area="City of Boston residents.",
   book_url=BOS_SPEC, phone="311 or 617-635-4500",
   source_urls=[BOS_SPEC, BOS_TRASH]),
 L(id="habitat-greater-boston-restore", name="Habitat for Humanity Greater Boston ReStore (West Roxbury)", type="drop-off",
   address="1580 VFW Parkway, West Roxbury, MA",
   items_accepted=["Bed frames, headboards & footboards", "Dressers, bureaus & armoires", "Coffee & end tables", "Desks (3' x 5' or smaller)", "Tables & chairs (not conference tables or dated)", "Upholstered furniture (not ripped, worn, broken, dated or faded)", "Outdoor furniture", "Appliances less than eight years old (fridges, washers, dryers, stoves, microwaves)", "Cabinets, doors, lighting, building materials"],
   items_not_accepted=["Mattresses & box springs", "Sofa beds", "Sofas with slip covers", "Futons", "Platform & trundle beds", "Hutches, sideboards, buffets, china cabinets", "TV armoires & entertainment centers", "Fitness equipment"],
   condition_rules="All donations must be in working order. Staff can refuse any item based on condition and store need. Email the ReStore for the current list.",
   stairs_inside="Drop-off: staff help unload at the store. In-home pickup is arranged through ReSupply (paid; see the ReSupply listing).",
   lead_time="Drop-off Tuesday to Saturday, 9:30 a.m. to 4:00 p.m. (as posted).",
   cost="Drop-off fee: not stated. Pickup is through ReSupply, a paid service.",
   service_area="Drop-off at the West Roxbury store. Habitat says a second ReStore is set to open in Watertown in fall 2026.",
   book_url="https://resupply.app.link/habitatbostonrestore", email="restore@habitatboston.org",
   source_urls=["https://habitatboston.org/restore/"]),
 L(id="resupply-boston", name="ReSupply donation pickup (Boston)", type="paid hauler",
   items_accepted=["Furniture (tables, dressers, bed frames, bookcases, etc.)", "Couches, sectionals, recliners, futons", "Mattresses", "Appliances", "Clothing, boxes & bags", "Office furniture"],
   condition_rules="Items should be clean, sturdy, complete, and usable (no broken frames, missing parts, or pet damage). Items the charity can't accept may carry a recycling fee, charged in $10 increments.",
   stairs_inside="Yes. Teams go up and down stairs; disassembly is available. Extra fees may apply.",
   lead_time="Priority pickups in 24 to 48 hours; small items in as little as one hour (per ReSupply's Boston page).",
   cost="Paid service. Starts at $19 (bags/boxes), $49 (small furniture and boxes), $99 (sofas and bulky furniture), plus a separate non-refundable booking fee. Final quote confirmed on site before loading.",
   service_area="Boston (enter your ZIP to confirm).",
   book_url="https://resupply.com/boston/",
   source_urls=["https://resupply.com/boston/furniture-donation-pickup/", "https://resupply.com/donate-furniture-in-boston/", "https://resupply.com/resources/donor-faq/"],
   notes="Habitat Greater Boston ReStore and Household Goods both point donors to ReSupply for in-home pickup."),
 L(id="furnishing-hope", name="Furnishing Hope of Massachusetts", type="furniture bank",
   address="131 Mount Auburn Street, Level B, Cambridge, MA 02138",
   items_accepted=["Mattresses & box springs", "Beds", "Dressers, night tables & armoires", "Sofas & upholstered chairs", "Coffee & end tables", "TV stands & entertainment centers", "Kitchen/dining tables & chairs", "Buffets, hutches, bookcases, cabinets"],
   condition_rules="New or gently used, clean, complete, and in good working condition. No stains, odors, or pet hair, major wear and tear, or anything needing repair. Send photos before scheduling.",
   stairs_inside="Pickup is handled by professional movers. Whether they go inside or upstairs is not stated, so check with them.",
   lead_time="Furniture drop-off in Acton on Tuesdays, Thursdays, and Saturdays, 9 a.m. to 12 p.m. Pickup timing: not stated.",
   cost="No pickup fee, but they request a tax-deductible donation, suggested at $250 to $400 depending on the size of the donation. Pickup requires at least six substantial furniture items.",
   service_area="Serves Boston-area families. Pickup area not stated, check with them.",
   book_url="https://www.furnishinghopema.org/donate-1", phone="(857) 229-7528", email="info@furnishinghopema.org",
   source_urls=["https://www.furnishinghopema.org/donate-1", "https://www.furnishinghopema.org/"]),
 L(id="household-goods-acton", name="Household Goods (Acton)", type="furniture bank",
   address="530 Main Street, Acton, MA",
   items_accepted=["Standard-size mattresses & box springs", "Bed frames (all parts) & bunk beds", "Dressers & armoires", "Couches, sofa beds & futons", "Chairs (no office chairs)", "Kitchen, dining, end & coffee tables", "Refrigerators, washers, electric dryers (newer than 10 years)", "Flat-screen TVs under 55\" (less than 10 years old)"],
   items_not_accepted=["Mattresses with any stains or rips", "Office furniture, desks, file cabinets", "Glass-top items", "Outdoor furniture", "Oversized or wall-mounted items"],
   condition_rules="Clean, complete, and in good working condition; nothing broken, chipped, torn, stained, or recalled.",
   stairs_inside="Volunteer pickup asks that items be in a garage or on the first floor if possible.",
   lead_time="Drop-off Tuesdays, Thursdays, and Saturdays, 9 a.m. to noon. Volunteer pickups typically scheduled 4+ weeks ahead. Paid pickups through ReSupply or ReMARKable Donations in as soon as 2 business days.",
   cost="Drop-off: not stated. Volunteer pickup: minimum $35 donation requested. Paid pickups (ReSupply / ReMARKable Donations): for a fee.",
   service_area="Volunteer pickup only in Acton, Boxborough, Carlisle, Concord, Littleton, Maynard, Stow, Sudbury, and Westford, so not Boston. Boston donors can drop off in Acton or use the paid pickup partners.",
   book_url="https://www.householdgoods.org/donate/donate-goods/pickup/", phone="978-763-1198",
   source_urls=["https://www.householdgoods.org/donate/donate-goods/donation-guidelines/", "https://www.householdgoods.org/donate/donate-goods/pickup/"]),
 L(id="thrift-shop-of-boston", name="The Thrift Shop of Boston (Roslindale)", type="charity pickup",
   address="33 Corinth Street, Roslindale, MA 02131",
   items_accepted=["Furniture (including antiques)", "Small appliances", "Smart flat-screen TVs", "Housewares, lamps, rugs, mirrors"],
   items_not_accepted=["Couches, futons & sleep sofas", "Beds: headboards, footboards, frames, mattresses, box springs", "Chairs with upholstery stains, tears or sun damage", "Office furniture, large desks", "TV armoires", "Older/CRT/rear-projection TVs", "Cribs"],
   condition_rules="Clean and in usable condition. Drop-off by appointment.",
   stairs_inside=NS,
   lead_time="Drop-off by appointment on Tuesdays, Thursdays, and Saturdays. Pickup timing: not stated.",
   cost="Furniture pickup has a fee that depends on location and volume, usually $50 to $150 (as posted).",
   service_area=NS,
   book_url="https://thriftshopofboston.org/donate-your-stuff/", phone="617-325-5300", email="thriftshopofboston@gmail.com",
   source_urls=["https://thriftshopofboston.org/donate-your-stuff/"],
   notes="Email photos, your location, and timeframe to request a furniture pickup. Proceeds support The Home for Little Wanderers."),
 L(id="savers-west-roxbury", name="Savers (West Roxbury) donation center", type="drop-off",
   address="1230 VFW Pkwy, West Roxbury, MA 02132",
   items_accepted=["Small furniture", "Small appliances", "Electronics", "Housewares", "Bed & bath"],
   condition_rules=NS, stairs_inside="No. Drop-off only.", lead_time="Store hours: see the store page.", cost=NS,
   service_area="Drop-off at the store.", book_url="https://stores.savers.com/ma/westroxbury/savers-thrift-store-1065.html", phone="(617) 323-9213",
   source_urls=["https://stores.savers.com/ma/westroxbury/savers-thrift-store-1065.html"],
   notes="Savers says it is a for-profit paid fundraiser accepting donations on behalf of Epilepsy Foundation New England."),
 L(id="salvation-army-satruck", name="The Salvation Army donation pickup (1-800-SA-TRUCK)", type="charity pickup",
   items_accepted=["Unbroken furniture: beds, sofas, chairs, tables, desks, cabinets (per national FAQ)", "Mattresses (per national FAQ)", "Working, non-built-in appliances (per national FAQ)"],
   condition_rules="Gently used and unbroken. The Salvation Army says accepted items vary by location; call 800-SA-TRUCK for local rules.",
   stairs_inside=NS, lead_time=NS,
   cost="Advertised as a free donation pickup on satruck.org. Local terms: check with them.",
   service_area="Enter a Boston ZIP on satruck.org to see whether pickup is offered at your address. I could not confirm Boston coverage on 2026-10-21.",
   book_url="https://satruck.org/", phone="1-800-728-7825",
   source_urls=["https://satruck.org/"]),
 L(id="boston-building-resources", name="Boston Building Resources (reuse center)", type="drop-off",
   address="100 Terrace St, Boston, MA 02120",
   items_accepted=["Building materials"],
   condition_rules="Fill out their Materials Donation Offer Form first (per the City of Boston directory).",
   stairs_inside="No. Drop-off (per the City of Boston directory).", lead_time=NS, cost=NS,
   service_area="Drop-off in Boston.", book_url="https://www.bostonbuildingresources.com/",
   source_urls=[BOS_CIRC],
   notes="Source is the City of Boston Circular Economy Directory (April 2024). I could not load the organization's own donation page on 2026-10-21."),
 L(id="loadup", name="LoadUp junk removal", type="paid hauler",
   items_accepted=["Furniture", "Mattresses", "Couches", "Appliances", "General junk"],
   condition_rules="No donation-quality requirement stated; this is junk removal.",
   stairs_inside="Yes. Full-service option removes items from inside (basement, attic, upstairs); curbside option also offered.",
   lead_time="Same-day pickup available in most areas and next-day almost everywhere else (per LoadUp's national page).",
   cost="Per LoadUp's national page: full-service from $75, curbside from $70, priority/same-day from $85. Guaranteed price shown before booking.",
   service_area="LoadUp says it serves all 50 states. Enter your Boston ZIP to confirm.",
   book_url="https://goloadup.com/junk-removal/",
   source_urls=["https://goloadup.com/junk-removal/"],
   notes="We do not currently have an affiliate relationship with LoadUp. If that changes, this listing will be labeled."),
 L(id="saatva-mattress-removal", name="Saatva old-mattress removal (with new Saatva delivery)", type="retailer haul-away",
   items_accepted=["Old mattress", "Old foundation / box spring"],
   condition_rules="Only with Saatva white-glove delivery when you select removal at checkout. Stained or damaged mattresses may be refused (per Saatva Help Center).",
   stairs_inside="Delivery and setup is in-home (white-glove). Removal details: see Saatva's help article.", lead_time="Happens on your new mattress delivery date.", cost=NS,
   service_area="Saatva delivery areas.", book_url="https://saatvahelp.saatva.com/hc/en-us/articles/360041763093-Does-Saatva-remove-my-old-mattress",
   source_urls=["https://saatvahelp.saatva.com/hc/en-us/articles/360041763093-Does-Saatva-remove-my-old-mattress"],
   notes="The City of Boston also suggests asking any mattress seller whether it will take your old mattress for recycling on delivery."),
]

haulers = [
 ("casa-blanca", "Casa Blanca Services Inc.", "82 Herbert St, Framingham, MA 01702 and 4 Bennett St, Everett, MA 02149", "508-271-5655", "https://casablancaservicesco.com/mattress-pick-up", "Pick-up. Schedule using the form on their website.", NS, "https://casablancaservicesco.com/"),
 ("handup", "HandUp Mattress Recycling & Upcycling", "127 Rodney French Blvd, New Bedford, MA 02744", "774-271-8744", "https://handupmattress.com/pages/curbside-mattress-pickup-program-terms-conditions", "Pick-up and drop-off.", "Drop-off $35 per mattress or box spring (as listed by the City). Pickup price: not stated, check with them.", "https://handupmattress.com/"),
 ("classic-cleanouts", "Classic Cleanouts", None, "781-558-2626", "https://classiccleanouts.com/junk-removal/mattress-disposal", "Pick-up. Free quote on their website.", "Free quote; price not stated.", "https://classiccleanouts.com/junk-removal/mattress-disposal"),
 ("green-mattress", "Green Mattress", "144 Field Street, Brockton, MA 02302", "781-720-9855", "https://www.greenmattressco.com/curbside", "Pick-up and drop-off. Drop off at their Brockton facility or schedule curbside pickup online.", NS, "https://www.greenmattressco.com/"),
 ("raw-material-recovery", "Raw Material Recovery Corp.", "461 West Broadway, Gardner, MA 01440", "978-730-8266", "http://www.rawmatrec.com/household-recycling-leominster-ma.html", "Drop-off center open to the public.", "See their monthly price sheet.", "http://www.rawmatrec.com/"),
 ("tough-stuff", "Tough Stuff Recycling", "145 Authority Drive, Fitchburg, MA 01420", "978-307-4118", "https://order.toughstuffrecycling.com/", "Pick-up and drop-off. Residential and commercial curbside pickup.", "Pickup $75 per mattress or box spring; drop-off $25 per mattress or box spring with proof of Boston residency or business (as listed by the City).", "https://toughstuffrecycling.com/"),
 ("mattress-pro", "Mattress Pro Recycling", "221 Jackson Street, Newton, MA 02459", "857-404-2496", "https://mattressprorecycling.com/schedule/", "Curbside pickup available 7 days a week; call or book online.", NS, "https://mattressprorecycling.com/"),
 ("junk-dispatch", "Junk Dispatch", None, "781-504-7480", "https://www.junkdispatch.com/mattressremoval", "Pick-up. Free quote by phone or website.", "Free quote; price not stated.", "https://www.junkdispatch.com/mattressremoval"),
 ("marvin", "Marvin Junk Removal", None, "781-267-5966", "https://marvinjunkremoval.net/marvin-junk-removal", "Pick-up. Free quote by phone or website.", "Free quote; price not stated.", "https://marvinjunkremoval.net/marvin-junk-removal"),
 ("burns", "Burns Cleanout & Junk Removal", "4 Harding Street, Lakeville, MA 02347", "774-260-1332", "https://burnscleanouts.com/", "Pick-up.", "$100 per mattress; senior and veteran discounts available (as listed by the City).", "https://burnscleanouts.com/"),
 ("lug-away", "Lug Away Junk Removal", None, "617-893-9824", "https://lugaway.com/service-areas/boston-ma/", "Pick-up. Curbside or inside the home.", "Curbside mattress pickup $124; inside home/apartment $174; king-size $245 (as listed by the City).", "https://lugaway.com/service-options/"),
 ("cc-junk", "CC Junk Removal & Hauling LLC", None, "774-284-5961", "https://www.cchaulsjunk.com/", "Pick-up; single or large-volume pickups for residents and property managers.", "$125 per mattress or box spring, indoor removal included (as listed by the City).", "https://www.cchaulsjunk.com/"),
 ("truck-taxi", "Truck Taxi Inc.", "51 Park Street, Dorchester, MA 02122", "800-332-6670", "https://trucktaxiinc.com/", "Pick-up. Call or use the website for a quote.", "Quote; price not stated.", "https://trucktaxiinc.com/"),
]
for hid, name, addr, phone, book, how, cost, site in haulers:
    stairs = NS
    if hid == "lug-away": stairs = "Yes. Inside-home pickup offered at a higher price (as listed by the City)."
    if hid == "cc-junk": stairs = "Yes. Indoor removal included (as listed by the City)."
    if hid in ("raw-material-recovery",): stairs = "No. Drop-off only."
    listings.append(L(id="mattress-" + hid, name=name, type="paid hauler", address=addr,
        items_accepted=["Mattresses", "Box springs"], condition_rules=how, stairs_inside=stairs, cost=cost,
        service_area="Serves Boston large residential buildings (7+ units), according to the City list. Confirm your address with them.",
        book_url=book, phone=phone, source_urls=[BOS_LARGE, site], notes=CITYLIST_NOTE))

city = {
 "slug": "boston", "name": "Boston", "state": "MA", "last_verified": D,
 "title": "How to Get Rid of a Couch, Mattress or Furniture in Boston (2026 Guide)",
 "meta_description": "Every verified way to get rid of a couch, mattress, furniture or appliance in Boston: City curbside & mattress pickup, ReStore, furniture banks, and paid haulers, with rules, costs and sources.",
 "intro": "Boston has free City options for furniture, mattresses and appliances, but each has its own rules. Here's what each option takes, what it costs (only where they publish it), and where we got the information.",
 "quick_answers": [
   {"q": "Couch or other furniture?", "a": "If you get City curbside trash collection, furniture can go out next to your bins on your regular collection day. To donate instead, check the ReStore and furniture banks below; most require clean, undamaged pieces."},
   {"q": "Mattress or box spring?", "a": "Mattresses are banned from Massachusetts trash. In a building with 6 units or fewer, book the City's free-of-appointment-fee curbside mattress pickup. In 7+ units, use your property manager or one of the mattress haulers below."},
   {"q": "Fridge, AC, TV or monitor?", "a": "Book a City special item collection. Remove fridge doors and all food first."},
   {"q": "Can't carry it to the curb?", "a": "City pickups are curbside only. Paid options that come inside include ReSupply (donation pickup), LoadUp, and several mattress haulers."}
 ],
 "resources": [
   {"label": "Boston Trash Day app & waste-sorting tool", "url": "https://www.boston.gov/departments/public-works/trash-and-recycling-day-schedule-and-search"},
   {"label": "Boston's Circular Economy Directory (PDF, City of Boston)", "url": BOS_CIRC},
   {"label": "Beyond the Bin search tool (RecycleSmartMA)", "url": "https://recyclesmartma.org/beyond-the-bin-search/"},
   {"label": "MassDEP waste disposal bans", "url": "https://www.mass.gov/guides/massdep-waste-disposal-bans"}
 ],
 "listings": listings,
}
# fix a wording slip: City pages state no fee; don't imply "free" beyond what's stated
city["quick_answers"][1]["a"] = "Mattresses are banned from Massachusetts trash. In a building with 6 units or fewer, book the City's curbside mattress pickup appointment (the City page mentions no fee). In 7+ units, use your property manager or one of the mattress haulers below."
json.dump(city, open("/workspace/bulky-directory/data/cities/boston.json", "w"), indent=2, ensure_ascii=False)
print(len(listings))
