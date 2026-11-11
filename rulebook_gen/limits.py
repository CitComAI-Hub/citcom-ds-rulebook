"""Request limits per buying organisation (rulebook R7.5).

Each class has a default; an offer can set its own `rate_limit = {count = N,
time_window = S}` in offers/*.toml. The gateway route of a provider serves every
offer under one path, so the limit is generated per path, and all the offers of a
path must agree. dataspace-on-upv puts it on the route as APISIX `limit-count`,
counted per issuer of the buyer's credential (the buying organisation), per route.
"""

DEFAULTS = {
    # reads of a provider's data: protects the source (Lepus reads VLCi live)
    "open-data": {"count": 60, "time_window": 60},
    "dataset-access": {"count": 60, "time_window": 60},
    # web services: a page loads its scripts, styles and images through the route
    "service-access": {"count": 600, "time_window": 60},
}


def of_offer(offer):
    limit = DEFAULTS[offer["class"]] | offer.get("rate_limit", {})
    if set(limit) != {"count", "time_window"} or not all(
        isinstance(v, int) and v > 0 for v in limit.values()
    ):
        raise ValueError(f"offer {offer['name']}: rate_limit needs positive integers count and time_window")
    return limit


def per_path(offers):
    """{path: {count, time_window}} for one provider."""
    out, by = {}, {}
    for offer in offers:
        limit = of_offer(offer)
        path = offer["path"]
        if path in out and out[path] != limit:
            raise ValueError(
                f"offers {by[path]} and {offer['name']} share {path} but have different rate limits"
            )
        out[path], by[path] = limit, offer["name"]
    return dict(sorted(out.items()))
