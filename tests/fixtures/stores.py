# json stores

valid_store = {
    "name": "test store",
    "description": "test",
    "delivery_range_km": 5,
    "shipping_cost": 10,
    "address": {
        "country_code": "AR",
        "type": "other",
        "street": "street 1",
        "street_number": "123",
        "city": "city 1",
        "region": "region 1",
    },
}

valid_store2 = {
    "name": "test store2",
    "description": "test2",
    "delivery_range_km": 5,
    "shipping_cost": 10,
    "address": {
        "country_code": "AR",
        "type": "other",
        "street": "street 2",
        "street_number": "123",
        "city": "city 2",
        "region": "region 2",
    },
}

invalid_store = {
    "name": "test",
    "description": "test",
    "delivery_range_km": -1,
    "shipping_cost": -1,
}
